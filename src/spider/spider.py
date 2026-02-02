import argparse
import asyncio
import os
import random
import sys
from datetime import datetime
from typing import Any, Literal, Optional
from urllib.parse import urlencode

from playwright.async_api import async_playwright, Page, TimeoutError, Locator

from src.agent.product_evaluator import ProductEvaluator
from src.config import get_config_instance
from src.env import STATE_FILE, RUNNING_IN_DOCKER
from src.notify.notify_manger import NotificationManager
from src.spider.parsers import pares_product_info_and_seller_info, pares_seller_detail_info
from src.task.result import save_task_result, get_result_filename, get_product_history_info
from src.task.task import get_all_tasks
from src.types import Seller, Task, TaskResult
from src.utils.logger import logger
from src.utils.utils import random_sleep, safe_get, extract_id_from_url_regex

DETAIL_API_URL_PATTERN = 'h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail'


class ValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class GoofishSpider:
    def __init__(
            self,
            task: Task,
            notification_manager: Optional['NotificationManager'] = None,
            product_evaluator: Optional[Any] = None,
            state_file: Optional[str] = None,
            browser_headless: bool = False,
            browser_channel: Literal['chrome', 'msedge', 'firefox'] = 'chrome',
    ):
        self.task = task
        self.output_filename = None
        self.processed_ids = set()
        self.notification_manager = notification_manager
        self.product_evaluator = product_evaluator
        self.history_prices = None

        self.state_file = state_file
        self.browser_headless = browser_headless
        self.browser_channel = browser_channel
        self.browser = None
        self.browser_context = None
        self.crawl_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._init_output_filename()

    def _init_output_filename(self):
        """初始化输出文件名"""
        task_id = self.task.get('task_id')
        self.output_filename = get_result_filename(task_id)
        logger.debug("输出文件名初始化为: {}", self.output_filename)

    async def get_history(self):
        """获取历史记录"""
        if os.path.exists(self.output_filename):
            logger.info("发现已存在文件 {}，正在加载历史记录...", self.output_filename)
            task_id = self.task.get('task_id')
            try:
                history_info = await get_product_history_info(task_id)
                self.history_prices = history_info['prices']
                self.processed_ids = history_info['processed']
                logger.info("加载完成，已记录 {} 个已处理过的商品。", len(self.processed_ids))
            except Exception as e:
                logger.error("读取历史文件时发生错误: {}", e)
        else:
            logger.info("输出文件 {} 不存在，将创建新文件。", self.output_filename)

        return len(self.processed_ids)

    @staticmethod
    def get_max_page(page_tiny: str) -> int:
        numbers = [int(x.strip()) for x in page_tiny.split('/')]
        return max(numbers)

    @staticmethod
    async def check_anti_spider_dialog(page: Page):
        dialogs = [
            ("div.baxia-dialog-mask", "baxia-dialog"),
            ("div.J_MIDDLEWARE_FRAME_WIDGET", "middleware-widget")
        ]

        for selector, dialog_type in dialogs:
            try:
                await page.locator(selector).wait_for(state='visible', timeout=2000)
                logger.warning("检测到 {} 反爬虫验证弹窗", dialog_type)
                return True
            except TimeoutError:
                pass

        logger.debug("未检测到任何反爬虫验证弹窗")
        return False

    async def process_product_list(self, product_list: list[Locator]):
        """处理单页商品列表"""
        logger.info("共有 {} 个商品，正在随机化处理顺序...", len(product_list))
        random.shuffle(product_list)
        logger.debug("随机化完成，将按随机顺序处理商品")

        detail_page = await self.browser_context.new_page()

        for i, item in enumerate(product_list):
            if os.getenv('DEBUG') and i > 1:
                logger.debug("DEBUG模式：仅处理前2个商品")
                return

            product_url = await item.get_attribute('href')
            logger.debug("商品连接: {}", product_url)

            product_id = extract_id_from_url_regex(product_url)
            if product_id is None:
                logger.warning("商品id提取失败")
                continue
            logger.debug("商品id提取成功: {}", product_id)

            if product_id in self.processed_ids:
                logger.info("商品 {} 已处理过，跳过", product_id)
                continue

            # 模拟用户操作得到新链接
            await item.dispatch_event('mousedown')
            await item.dispatch_event('mousemove')
            await item.dispatch_event('mouseup')

            real_url = await item.get_attribute('href')
            logger.debug("真实点击链接: {}", real_url)

            async with detail_page.expect_response(lambda r: DETAIL_API_URL_PATTERN in r.url,
                                                   timeout=25000) as detail_info:
                await detail_page.goto(real_url, wait_until="domcontentloaded", timeout=25000)
                try:
                    detail_response = await detail_info.value
                    if detail_response.ok:
                        await self.process_product(
                            await detail_response.json(),
                            {
                                'product_id': product_id,
                                'product_url': product_url,
                            }
                        )
                        self.processed_ids.add(product_id)
                except ValidationError as e:
                    raise e
                except TimeoutError:
                    logger.warning("超时：无法获取商品 {} 的详细信息", product_id)
                except Exception as e:
                    logger.error("处理商品 {} 时出错：{}", product_id, e)

            await random_sleep(5, 10)

        await random_sleep(5, 10)
        await detail_page.close()

    async def process_product(self, product_api_data, base_product_info):
        """处理商品详情页"""
        product_id = base_product_info.get('product_id')
        logger.info("开始处理商品 {}", product_id)

        ret_string = str(safe_get(product_api_data, 'ret', default=[]))

        if "FAIL_SYS_USER_VALIDATE" in ret_string:
            raise ValidationError('FAIL_SYS_USER_VALIDATE')

        product_info, seller_base_info = pares_product_info_and_seller_info(product_api_data, base_product_info)

        seller_info = await self.process_seller(seller_base_info)

        keyword = self.task.get('keyword', '')
        task_id = self.task.get('task_id')

        final_record: TaskResult = {
            "爬取时间": self.crawl_time,
            "搜索关键字": keyword,
            "任务名称": self.task.get('task_name', 'Untitled Task'),
            "商品信息": product_info,
            "卖家信息": seller_info
        }
        if self.product_evaluator:
            logger.info("开始AI分析")
            try:
                analysis_results = await self.product_evaluator.evaluate(
                    product=product_info,
                    seller=seller_info,
                    history_prices=self.history_prices,
                    target_product={"description": self.task.get('description')}
                )
                final_record['分析结果'] = analysis_results
            except Exception as e:
                logger.error("AI分析出错: {}", e)
        else:
            logger.warning("AI分析为启用或未配置")

        logger.info("开始写入数据")
        save_task_result(task_id, final_record)

        if self.notification_manager:
            logger.info("开始推送通知")
            self.notification_manager.notify(final_record)

    async def process_seller(self, seller_info: Seller):
        """处理卖家信息"""
        seller_id = seller_info['卖家ID']
        logger.info("开始采集用户ID: {} 的完整信息...", seller_id)
        page = await self.browser_context.new_page()
        async with page.expect_response(lambda r: "mtop.idle.web.user.page.head" in r.url,
                                        timeout=25000) as detail_info:
            await page.goto(f"https://www.goofish.com/personal?userId={seller_id}", wait_until="domcontentloaded",
                            timeout=20000)
            detail_response = await detail_info.value
            if detail_response.ok:
                seller_info = pares_seller_detail_info(await detail_response.json(), seller_info)
        await random_sleep(5, 10)
        await page.close()
        return seller_info

    async def run(self):
        """执行爬虫任务"""
        keyword = self.task.get('keyword')
        max_pages = self.task.get('max_pages', 1)
        personal_only = self.task.get('personal_only', False)
        min_price = self.task.get('min_price')
        max_price = self.task.get('max_price')

        last_processed_count = await self.get_history()

        async with async_playwright() as p:
            # 尽量模拟真实浏览器，不要使用 js 打补丁的方式
            self.browser = await p.chromium.launch(
                headless=self.browser_headless,
                channel=self.browser_channel
            )
            version = self.browser.version
            # 使用真实版本号
            user_agent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version.split('.')[0]} Safari/537.36'
            self.browser_context = await self.browser.new_context(
                storage_state=self.state_file,
                viewport={"width": 1920, "height": 957},
                screen={'width': 1920, 'height': 1080},
                device_scale_factor=1.0,
                user_agent=user_agent,
                is_mobile=False,
                has_touch=False,
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                permissions=["notifications"]
            )

            page = await self.browser_context.new_page()

            try:
                logger.info("步骤 1 - 直接导航到搜索结果页...")
                params = {'q': keyword}
                search_url = f"https://www.goofish.com/search?{urlencode(params)}&spm=a21ybx.home.searchInput.0"
                logger.debug("目标URL: {}", search_url)

                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector('text=新发布', timeout=15000)

                if await self.check_anti_spider_dialog(page):
                    raise ValidationError('反爬虫验证弹窗')

                try:
                    await page.click("div[class*='closeIconBg']", delay=random.uniform(10, 20), timeout=3000)
                    logger.info("已关闭广告弹窗。")
                except TimeoutError:
                    logger.debug("未检测到广告弹窗。")

                logger.info("步骤 2 - 应用筛选条件...")

                await page.hover('text=新发布')
                await random_sleep(0.5, 2)

                await page.click('text=最新', delay=random.uniform(10, 20))
                await random_sleep(3, 5)

                if personal_only:
                    await page.click('text=个人闲置', delay=random.uniform(10, 20))
                    await random_sleep(2, 4)
                    logger.debug("已筛选个人闲置商品")

                if min_price or max_price:
                    price_container = page.locator('div[class*="search-price-input-container"]').first
                    if await price_container.is_visible():
                        if min_price:
                            await price_container.get_by_placeholder("¥").first.fill(min_price)
                            await random_sleep(1, 2.5)
                            logger.debug("设置最低价格: {}", min_price)
                        if max_price:
                            await price_container.get_by_placeholder("¥").nth(1).fill(max_price)
                            await random_sleep(1, 2.5)
                            logger.debug("设置最高价格: {}", max_price)

                        await page.keyboard.press('Tab')
                        await random_sleep(4, 7)
                        logger.debug("价格筛选已应用")

                    else:
                        logger.warning("未找到价格输入容器。")

                logger.info("所有筛选已完成")

                page_tiny = await page.locator('span[class*="search-page-tiny-page"]').first.text_content()
                page_btn = await page.locator('div[class*="search-pagination-page-box"]').all()

                o_max_page = self.get_max_page(page_tiny)
                max_page = min(o_max_page, max_pages)

                logger.info("共有 {} 页，设置最大处理 {} 页，实际需处理 {} 页", o_max_page, max_pages, max_page)

                for page_num in range(1, max_pages + 1):
                    try:
                        logger.info("正在处理第 {}/{} 页", page_num, max_pages)
                        await page_btn[page_num - 1].click(delay=random.uniform(10, 20))
                        await random_sleep(10, 20)
                        product_list = await page.locator('a[class*="feeds-item-wrap"]').all()
                        await self.process_product_list(product_list)
                    except ValidationError as e:
                        raise e
                    except Exception as e:
                        logger.error("第 {}/{} 页处理失败: {}", page_num, max_pages, e)

            except ValidationError as e:
                logger.error("==================== CRITICAL BLOCK DETECTED ====================")
                logger.error("检测到闲鱼反爬虫验证 ({})，程序将终止。", e)
                long_sleep_duration = random.randint(300, 600)
                logger.warning("为避免账户风险，将执行一次长时间休眠 ({} 秒) 后再退出...", long_sleep_duration)
                await asyncio.sleep(long_sleep_duration)
                logger.info("长时间休眠结束，现在将安全退出。")
                logger.error("===================================================================")
                logger.info("触发闲鱼反爬虫机制，将关闭浏览器")
            except Exception as e:
                logger.error("程序发生错误: {}", e)

            await self.browser.close()

        new_processed_count = len(self.processed_ids) - last_processed_count
        logger.info("任务完成，本次运行共处理了 {} 个新商品", new_processed_count)
        return new_processed_count


async def main(debug: bool = False):
    parser = argparse.ArgumentParser(
        description="闲鱼商品监控脚本，支持多任务配置和实时AI分析。",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--debug", type=bool, default=False, help="调试模式：每个任务仅处理每页前 2 个新商品")
    parser.add_argument("--task-id", type=int, default=None, help="运行指定id的单个任务 (用于定时任务调度)")

    args = parser.parse_args()

    if args.debug or debug:
        os.environ["DEBUG"] = "1"
        logger.debug_mode = True
        logger.info("DEBUG模式已启用")

    if not os.path.exists(STATE_FILE):
        logger.warning("登录状态文件 '{}' 不存在", STATE_FILE)

    tasks = await get_all_tasks()

    active_tasks = []

    if args.task_id is not None:
        task = next((it for it in tasks if it['task_id'] == args.task_id), None)
        if not task:
            logger.error(f"未找到id为 '{args.task_id}' 的任务")
            sys.exit(f"错误: 任务 '{args.task_id}' 不存在")

        active_tasks.append(task)
        logger.info("将执行单个任务: {} (ID: {})", task['task_name'], args.task_id)

    else:
        active_tasks = [task for task in tasks if task.get('enabled', False)]
        logger.info("找到 {} 个启用的任务", len(active_tasks))

    if not active_tasks:
        logger.info("没有需要执行的任务，程序退出。")
        return

    config = get_config_instance()

    notification_manager = None
    if config.is_notifications_enabled:
        notification_manager = await NotificationManager.create_from_config(config.notifications_config)

    product_evaluator = None
    if config.is_evaluator_enabled:
        product_evaluator = await ProductEvaluator.create_from_config(config.evaluator_config)

    coroutines = []
    for task in active_tasks:
        logger.info("任务 '{}' 已加入执行队列。", task['task_name'])
        spider = GoofishSpider(
            task=task,
            notification_manager=notification_manager,
            product_evaluator=product_evaluator,
            state_file=STATE_FILE,
            browser_headless=True if RUNNING_IN_DOCKER else config.browser_headless,
            browser_channel='chromium-headless-shell' if RUNNING_IN_DOCKER else config.browser_channel
        )
        coroutines.append(spider.run())

    results = await asyncio.gather(*coroutines, return_exceptions=True)

    logger.info("所有任务执行完毕")

    for i, result in enumerate(results):
        task_name = active_tasks[i]['task_name']
        if isinstance(result, Exception):
            logger.error("任务 '{}' 因异常而终止: {}", task_name, result)
        else:
            logger.info("任务 '{}' 正常结束，本次运行共处理了 {} 个新商品。", task_name, result)


if __name__ == "__main__":
    asyncio.run(main())
