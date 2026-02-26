import os
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext
from playwright_stealth import Stealth

from src.config import get_config_instance
from src.env import RUNNING_IN_DOCKER


@dataclass
class BrowserInstance:
    """承载浏览器和上下文的容器"""
    browser: Browser
    context: BrowserContext


@asynccontextmanager
async def create_browser(state_file: Optional[str] = None):
    config = get_config_instance()
    headless = True if RUNNING_IN_DOCKER else config.browser_headless
    channel = 'chromium-headless-shell' if RUNNING_IN_DOCKER else config.browser_channel

    playwright = None
    browser = None
    context = None

    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=headless,
            channel=channel
        )
        version = browser.version
        major_version = version.split('.')[0] if version else "122"
        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36"
        context = await browser.new_context(
            storage_state=state_file if (state_file and os.path.exists(state_file)) else None,
            viewport={"width": 1920, "height": 957},
            screen={'width': 1920, 'height': 1080},
            user_agent=user_agent,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
        )

        await Stealth(
            navigator_languages_override=('zh-CN', 'zh'),
            init_scripts_only=True
        ).apply_stealth_async(context)

        context.set_default_timeout(30_000)

        yield BrowserInstance(browser=browser, context=context)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


async def check_browser_purity():
    async with create_browser() as p:
        page = await p.context.new_page()
        await page.goto('https://bot.sannysoft.com/', wait_until="networkidle")
        await page.wait_for_timeout(1000)
        html_content = await page.content()
        html_content = re.sub(r'<script\b[^>]*>([\s\S]*?)</script>', '', html_content)
        return html_content
