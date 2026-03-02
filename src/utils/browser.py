import asyncio
import os
import re
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

from src.config import get_config_instance
from src.env import RUNNING_IN_DOCKER
from src.utils.logger import logger


@dataclass
class BrowserInstance:
    """承载浏览器和上下文的容器"""
    browser: Browser
    context: BrowserContext
    playwright: Playwright  # 持有引用以便手动 stop


class BrowserManager:
    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

        config = get_config_instance()

        self.headless = True if RUNNING_IN_DOCKER else config.browser_headless
        self.channel = 'chromium-headless-shell' if RUNNING_IN_DOCKER else config.browser_channel

    async def start(self, *, headless=None, channel=None) -> BrowserInstance:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless if headless is None else headless,
            channel=self.channel if channel is None else channel,
        )
        version = self.browser.version
        major_version = version.split('.')[0] if version else "122"
        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36"

        self.context = await self.browser.new_context(
            storage_state=self.state_file if (self.state_file and os.path.exists(self.state_file)) else None,
            viewport={"width": 1920, "height": 957},
            screen={'width': 1920, 'height': 1080},
            user_agent=user_agent,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
        )

        from playwright_stealth import Stealth
        await Stealth(
            navigator_languages_override=('zh-CN', 'zh'),
            init_scripts_only=True
        ).apply_stealth_async(self.context)

        self.context.set_default_timeout(30_000)

        return BrowserInstance(
            browser=self.browser,
            context=self.context,
            playwright=self.playwright
        )

    async def stop(self):
        try:
            if self.context:
                if self.state_file:
                    await self.context.storage_state(path=self.state_file)
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"浏览器清理时发生错误: {e}")
        finally:
            await asyncio.sleep(1)

    async def __aenter__(self) -> BrowserInstance:
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


def create_browser(state_file: Optional[str] = None) -> BrowserManager:
    return BrowserManager(state_file)


async def check_browser_purity():
    async with create_browser() as p:
        page = await p.context.new_page()
        await page.goto('https://bot.sannysoft.com/', wait_until="networkidle")
        await page.wait_for_timeout(1000)
        html_content = await page.content()
        html_content = re.sub(r'<script\b[^>]*>([\s\S]*?)</script>', '', html_content)
        return html_content
