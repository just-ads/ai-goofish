import argparse
import json
import asyncio
import os
import random
import zstandard
import sys
from typing import Literal, Optional, Tuple
from urllib.parse import urlencode

from playwright.async_api import async_playwright, Page, TimeoutError, Locator

from src.agent.product_evaluator import ProductEvaluator
from src.config import get_config_instance
from src.env import STATE_FILE, RUNNING_IN_DOCKER
from src.notify.notify_manger import NotificationManager
from src.spider.parsers import pares_product_info_and_seller_info, pares_seller_detail_info
from src.task.record import add_task_record
from src.task.result import save_task_result, get_result_filename, get_product_history_info
from src.task.task import get_tasks
from src.types import Seller, Task, TaskResult
from src.utils.date import now_str
from src.utils.logger import logger
from src.utils.utils import random_sleep, extract_id_from_url_regex


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
            product_evaluator: Optional['ProductEvaluator'] = None,
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
        self.crawl_time = now_str()
        self._init_output_filename()

    def _init_output_filename(self):
        """初始化输出文件名"""
        task_id = self.task.get('task_id')
        self.output_filename = get_result_filename(task_id)
        logger.debug(f"输出文件名初始化为: {self.output_filename}")

    async def get_history(self):
        """获取历史记录"""
        if os.path.exists(self.output_filename):
            logger.info(f"发现已存在文件 {self.output_filename}，正在加载历史记录...")
            task_id = self.task.get('task_id')
            try:
                history_info = await get_product_history_info(task_id)
                self.history_prices = history_info['prices']
                self.processed_ids = history_info['processed']
                logger.info(f"加载完成，已记录 {len(self.processed_ids)} 个已处理过的商品。")
            except Exception as e:
                logger.error(f"读取历史文件时发生错误: {e}")
        else:
            logger.info(f"输出文件 {self.output_filename} 不存在，将创建新文件。")

        return len(self.processed_ids)

    @staticmethod
    def get_max_page(page_tiny: str) -> int:
        numbers = [int(x.strip()) for x in page_tiny.split('/')]
        return max(numbers)

    @staticmethod
    async def check_anti_spider_dialog(page: Page):
        logger.info('检测反爬虫弹窗')

        dialogs = [
            ("div.baxia-dialog-mask", "baxia-dialog"),
            ("div.J_MIDDLEWARE_FRAME_WIDGET", "middleware-widget")
        ]

        for selector, dialog_type in dialogs:
            try:
                if await page.locator(selector).is_visible(timeout=4_000):
                    logger.warning(f"当前页面检测到 {dialog_type} 反爬虫验证弹窗")
                    return True
            except TimeoutError:
                pass

        logger.info("未检测到反爬虫弹窗")
        return False

    async def goto(self, page: Page, page_url: str):
        await page.goto(page_url, wait_until="domcontentloaded", timeout=30_000)

        if await self.check_anti_spider_dialog(page):
            raise ValidationError('反爬虫验证弹窗')

        try:
            await page.click("div[class*='closeIconBg']", delay=random.uniform(10, 20), timeout=4_000)
            logger.info("已关闭广告弹窗。")
        except TimeoutError:
            logger.info("未检测到广告弹窗。")

    @staticmethod
    async def _parse_response_body(response):
        """解析响应 body，增强对 zstd 的容错性, 增加对『假压缩』的识别"""
        try:
            raw = await asyncio.wait_for(response.body(), timeout=10)
            if not raw:
                raise ValueError('接口获取数据出错')

            if raw.startswith(b'\x7b') or raw.startswith(b'\x5b'):
                data = json.loads(raw)
            else:
                encoding = response.headers.get('content-encoding', '').lower()
                if 'zstd' in encoding:
                    dctx = zstandard.ZstdDecompressor()
                    try:
                        # 方案 A: 尝试直接解压
                        decompressed = dctx.decompress(raw)
                    except zstandard.ZstdError:
                        # 方案 B: 针对无法确定大小的 Frame Header，限制最大输出进行解压
                        decompressed = dctx.decompress(raw, max_output_size=10 * 1024 * 1024)
                    data = json.loads(decompressed)
                else:
                    data = json.loads(raw)

            if "FAIL_SYS_USER_VALIDATE" in str(data):
                raise ValidationError('FAIL_SYS_USER_VALIDATE')

            return data

        except asyncio.TimeoutError:
            content_length = response.headers.get('Content-Length')
            te = response.headers.get('Transfer-Encoding')

            if content_length:
                msg = f"超大body ({content_length} bytes)"
            elif te == 'chunked':
                msg = "HTTP 慢速陷阱"
            else:
                msg = "未知网络风险"

            logger.error(f"解析超时: {msg}")
            raise ValidationError(f'body 解析超时({msg})')

        except Exception as e:
            logger.error(f"解析异常: {str(e)}")
            raise ValidationError(f"数据解析失败: {str(e)}")

    async def goto_and_expect(self, page: Page, page_url: str, url_or_predicate):
        response_task = page.expect_response(url_or_predicate, timeout=60_000)
        await self.goto(page, page_url)
        async with response_task as response_info:
            response = await response_info.value
            try:
                data = await self._parse_response_body(response)
            except ValidationError as e:
                await page.close()
                raise e

            return data

    async def process_seller(self, seller_info: Seller):
        """处理卖家信息"""
        seller_id = seller_info['卖家ID']
        logger.info(f"开始采集用户ID: {seller_id} 的完整信息...")
        page = await self.browser_context.new_page()

        data = await self.goto_and_expect(
            page=page,
            page_url=f"https://www.goofish.com/personal?userId={seller_id}",
            url_or_predicate=lambda r: "mtop.idle.web.user.page.head" in r.url
        )
        seller_info = pares_seller_detail_info(data, seller_info)

        await random_sleep(5, 10)
        await page.close()
        return seller_info

    async def process_product_list(self, product_list: list[Locator]):
        """处理单页商品列表"""
        logger.info(f"共有 {len(product_list)} 个商品，正在随机化处理顺序...")
        random.shuffle(product_list)
        logger.debug("随机化完成，将按随机顺序处理商品")

        detail_page = await self.browser_context.new_page()

        for i, item in enumerate(product_list):
            if os.getenv('DEBUG') and i > 1:
                logger.debug("DEBUG模式：仅处理前2个商品")
                return

            product_url = await item.get_attribute('href')
            logger.debug(f"商品连接: {product_url}")

            product_id = extract_id_from_url_regex(product_url)
            if product_id is None:
                logger.warning("商品id提取失败")
                continue
            logger.debug(f"商品id提取成功: {product_id}")

            if product_id in self.processed_ids:
                logger.info(f"商品 {product_id} 已处理过，跳过")
                continue

            logger.info(f"获取商品 {product_id} 的详细信息")

            # 模拟用户操作得到新链接
            await item.dispatch_event('mousedown')
            await item.dispatch_event('mousemove')
            await item.dispatch_event('mouseup')

            real_url = await item.get_attribute('href')
            logger.debug(f"真实点击链接: {real_url}")

            try:
                base_product_info = {
                    'product_id': product_id,
                    'product_url': product_url,
                }
                data = await self.goto_and_expect(
                    page=detail_page,
                    page_url=real_url,
                    url_or_predicate=lambda r: 'h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail' in r.url
                )
                await self.process_product(data, base_product_info)
                self.processed_ids.add(product_id)

            except TimeoutError:
                logger.warning(f"超时：无法获取商品 {product_id} 的详细信息")
            except ValidationError:
                raise
            except Exception as e:
                logger.error(f"处理商品 {product_id} 时出错：{e}")

            await random_sleep(5, 10)

        await random_sleep(5, 10)
        await detail_page.close()

    async def process_product(self, product_api_data, base_product_info):
        """处理商品详情页"""
        product_id = base_product_info.get('product_id')
        logger.info(f"开始处理商品 {product_id}")

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
                logger.error(f"AI分析出错: {e}")
        else:
            logger.warning("AI分析未启用或未配置")

        logger.info("开始写入数据")
        save_task_result(task_id, final_record)

        if self.notification_manager:
            logger.info("开始推送通知")
            self.notification_manager.notify(final_record)

    async def run(self) -> Tuple[Literal['normal', 'abnormal', 'risk'], int]:
        """执行爬虫任务"""
        last_processed_count = 0

        try:
            keyword = self.task.get('keyword')
            max_pages = self.task.get('max_pages', 1)
            personal_only = self.task.get('personal_only', False)
            min_price = self.task.get('min_price')
            max_price = self.task.get('max_price')

            last_processed_count = await self.get_history()

            ret_type: Literal['normal', 'abnormal', 'risk'] = 'normal'
            async with async_playwright() as p:
                try:
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

                    self.browser_context.set_default_timeout(30_000)

                    page = await self.browser_context.new_page()

                    logger.info("步骤 1 - 直接导航到搜索结果页...")
                    params = {'q': keyword}
                    search_url = f"https://www.goofish.com/search?{urlencode(params)}&spm=a21ybx.home.searchInput.0"
                    logger.debug(f"目标URL: {search_url}")

                    await self.goto(page, search_url)

                    logger.info("步骤 2 - 应用筛选条件...")

                    await page.click('text=新发布')
                    await random_sleep(1, 3)

                    await page.click('text=最新', delay=random.uniform(10, 20))
                    await random_sleep(3, 5)

                    if personal_only:
                        await page.click('text=个人闲置', delay=random.uniform(10, 20))
                        await random_sleep(2, 4)
                        logger.debug("已筛选个人闲置商品")

                    if min_price or max_price:
                        price_container = page.locator('div[class*="search-price-input-container"]').first
                        if await price_container.is_visible():
                            price_inputs = price_container.get_by_placeholder("¥")
                            if min_price:
                                min_price_input = price_inputs.first
                                await min_price_input.click(delay=random.uniform(10, 20))
                                await min_price_input.fill(min_price)
                                await random_sleep(1, 2.5)
                                logger.debug(f"设置最低价格: {min_price}")
                            if max_price:
                                max_price_input = price_inputs.nth(1)
                                await max_price_input.click(delay=random.uniform(10, 20))
                                await max_price_input.fill(max_price)
                                await random_sleep(1, 2.5)
                                logger.debug(f"设置最高价格: {max_price}")

                            await page.keyboard.press('Tab')
                            await random_sleep(4, 7)
                            logger.debug("价格筛选已应用")

                        else:
                            logger.warning("未找到价格输入容器。")

                    logger.info("所有筛选已完成")

                    page_tiny = await page.locator('span[class*="search-page-tiny-page"]').first.text_content()
                    page_btn = await page.locator('div[class*="search-pagination-page-box"]').all()

                    o_max_page = self.get_max_page(page_tiny)
                    c_max_pages = min(o_max_page, max_pages)

                    logger.info(f"共有 {o_max_page} 页，设置最大处理 {max_pages} 页，实际需处理 {c_max_pages} 页")

                    for page_num in range(1, c_max_pages + 1):
                        try:
                            logger.info(f"正在处理第 {page_num}/{c_max_pages} 页")
                            await page_btn[page_num - 1].click(delay=random.uniform(10, 20))
                            await random_sleep(10, 20)
                            product_list = await page.locator('a[class*="feeds-item-wrap"]').all()
                            await self.process_product_list(product_list)
                        except ValidationError:
                            raise
                        except Exception as e:
                            logger.error(f"第 {page_num}/{c_max_pages} 页处理失败: {e}")

                except ValidationError as e:
                    logger.warning("==================== CRITICAL BLOCK DETECTED ====================")
                    logger.warning(f"检测到闲鱼反爬虫验证 ({e})，程序将终止。")
                    long_sleep_duration = random.randint(300, 600)
                    logger.warning(f"为避免账户风险，将执行一次长时间休眠 ({long_sleep_duration} 秒) 后再退出...")
                    await asyncio.sleep(long_sleep_duration)
                    logger.warning("长时间休眠结束，现在将安全退出。")
                    logger.warning("===================================================================")
                    logger.warning("触发闲鱼反爬虫机制，将关闭浏览器")
                    ret_type = 'risk'

                await self.browser.close()

        except Exception as e:
            logger.error(f"程序发生错误: {e}")
            ret_type = 'abnormal'

        new_processed_count = len(self.processed_ids) - last_processed_count
        logger.info(f"任务完成，本次运行共处理了 {new_processed_count} 个新商品")

        return ret_type, new_processed_count


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
        logger.warning(f"登录状态文件 '{STATE_FILE}' 不存在")

    tasks = await get_tasks()

    active_tasks = []

    if args.task_id is not None:
        task = next((it for it in tasks if it['task_id'] == args.task_id), None)
        if not task:
            logger.error(f"未找到id为 '{args.task_id}' 的任务")
            sys.exit(f"错误: 任务 '{args.task_id}' 不存在")

        active_tasks.append(task)
        logger.info(f"将执行单个任务: {task['task_name']} (ID: {args.task_id})")

    else:
        active_tasks = [task for task in tasks if task.get('enabled', False)]
        logger.info(f"找到 {len(active_tasks)} 个启用的任务")

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
        logger.info(f"任务 '{task['task_name']}' 已加入执行队列。")
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
        task = active_tasks[i]
        task_name = task['task_name']
        if isinstance(result, Exception):
            logger.error(f"任务 '{task_name}' 因异常而终止: {result}")
            await add_task_record(task['task_id'], 'abnormal')
        else:
            await add_task_record(task['task_id'], result[0])
            logger.info(f"任务 '{task_name}' 结束，结束类型{result[0]}， 本次运行共处理了 {result[1]} 个新商品。")


if __name__ == "__main__":
    asyncio.run(main())
