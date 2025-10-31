import argparse
import asyncio
import json
import os
import random
import sys
from datetime import datetime
from urllib.parse import urlencode

from playwright.async_api import async_playwright, Page, TimeoutError

from src.agent.client import ai_client
from src.agent.product_evaluator import ProductEvaluator
from src.config import STATE_FILE, RUN_HEADLESS, USE_EDGE, RUNNING_IN_DOCKER, API_URL_PATTERN, DETAIL_API_URL_PATTERN, SKIP_AI_ANALYSIS
from src.notify.notify_manger import NotificationManager
from src.spider.parsers import parse_page, pares_product_detail_and_seller_info, pares_seller_detail_info
from src.task.result import save_task_result
from src.task.task import Task
from src.utils.utils import random_sleep, safe_get


class ValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class GoofishSpider:
    def __init__(self, task: Task, notification_manager: NotificationManager):
        self.task = task
        self.output_filename = None
        self.processed_ids = set()
        self.notification_manager = notification_manager
        self.browser = None
        self.browser_context = None

        # 初始化输出文件名
        self._init_output_filename()

    def _init_output_filename(self):
        """初始化输出文件名"""
        keyword = self.task.get('keyword')
        self.output_filename = os.path.join("jsonl", f"{keyword.replace(' ', '_')}_full_data.jsonl")

    def get_history(self):
        """获取历史记录"""
        if os.path.exists(self.output_filename):
            print(f"LOG: 发现已存在文件 {self.output_filename}，正在加载历史记录以去重...")
            try:
                with open(self.output_filename, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            record = json.loads(line)
                            product_id = record.get('商品信息', {}).get('商品ID', '')
                            self.processed_ids.add(product_id)
                        except json.JSONDecodeError:
                            print(f"   [警告] 文件中有一行无法解析为JSON，已跳过。")
                print(f"LOG: 加载完成，已记录 {len(self.processed_ids)} 个已处理过的商品。")
            except IOError as e:
                print(f"[警告] 读取历史文件时发生错误: {e}")
        else:
            print(f"LOG: 输出文件 {self.output_filename} 不存在，将创建新文件。")

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
                print(f"检测到 {dialog_type} 反爬虫验证弹窗")
                return True
            except TimeoutError:
                pass

        print("\nLOG: 未检测到任何反爬虫验证弹窗")
        return False

    async def process_page(self, page_data: dict):
        """处理单页商品列表"""
        product_basic_info = parse_page(page_data)

        detail_page = await self.browser_context.new_page()
        print(f'共有 {len(product_basic_info)} 个商品')

        for i, item in enumerate(product_basic_info):
            if os.getenv('DEBUG') and i > 1:
                await detail_page.close()
                return
            product_id = item.get('商品ID')
            if product_id in self.processed_ids:
                continue

            product_url = item.get('商品链接')

            async with detail_page.expect_response(lambda r: DETAIL_API_URL_PATTERN in r.url, timeout=25000) as detail_info:
                await detail_page.goto(product_url, wait_until="domcontentloaded", timeout=25000)

                try:
                    detail_response = await detail_info.value
                    if detail_response.ok:
                        await self.process_product(await detail_response.json(), item)
                        self.processed_ids.add(product_id)  # 处理成功后添加到已处理集合
                except ValidationError as e:
                    raise e
                except TimeoutError:
                    print(f"超时：无法获取商品 {product_id} 的详细信息")
                except Exception as e:
                    print(f"处理商品 {product_id} 时出错：{e}")

            await random_sleep(5, 10)

        await detail_page.close()

    async def process_product(self, product_api_data, base_data):
        """处理商品详情页"""
        print(f'开始处理商品 {base_data["商品标题"][0:10]}')

        ret_string = str(safe_get(product_api_data, 'ret', default=[]))

        if "FAIL_SYS_USER_VALIDATE" in ret_string:
            raise ValidationError('FAIL_SYS_USER_VALIDATE')

        product_data, seller_base_info = pares_product_detail_and_seller_info(product_api_data, base_data)

        seller_info = await self.process_seller(seller_base_info)

        keyword = self.task.get('keyword')

        final_record = {
            "爬取时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "搜索关键字": keyword,
            "任务名称": self.task.get('task_name', 'Untitled Task'),
            "商品信息": product_data,
            "卖家信息": seller_info
        }

        if (not SKIP_AI_ANALYSIS) and ai_client:
            print('开始ai分析')
            try:
                product_evaluator = ProductEvaluator(
                    ai_client,
                    product_data,
                    seller_info,
                    {"description": self.task.get('description')}
                )
                analysis_results = await product_evaluator.evaluate()
                final_record['分析结果'] = analysis_results
            except Exception as e:
                print(f'ai分析出错: {e}')
        print('写入数据')
        save_task_result(keyword, final_record)
        print('推送通知')
        self.notification_manager.notify(final_record)

    async def process_seller(self, seller_info: dict):
        """处理卖家信息"""
        print(f"   -> 开始采集用户ID: {seller_info['卖家ID']} 的完整信息...")
        page = await self.browser_context.new_page()
        async with page.expect_response(lambda r: "mtop.idle.web.user.page.head" in r.url, timeout=25000) as detail_info:
            await page.goto(f"https://www.goofish.com/personal?userId={seller_info['卖家ID']}", wait_until="domcontentloaded", timeout=20000)
            detail_response = await detail_info.value
            if detail_response.ok:
                seller_info = pares_seller_detail_info(await detail_response.json(), seller_info)
        await page.close()
        return seller_info

    async def run(self):
        """执行爬虫任务"""
        keyword = self.task.get('keyword')
        max_pages = self.task.get('max_pages', 1)
        personal_only = self.task.get('personal_only', False)
        min_price = self.task.get('min_price')
        max_price = self.task.get('max_price')

        has_state_file = os.path.exists(STATE_FILE)

        last_processed_count = self.get_history()

        async with async_playwright() as p:
            self.browser = await p.chromium.launch(
                headless=RUN_HEADLESS,
                channel="msedge" if USE_EDGE else "chrome" if not RUNNING_IN_DOCKER else None
            )
            self.browser_context = await self.browser.new_context(
                storage_state=STATE_FILE if has_state_file else None,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            )

            page = await self.browser_context.new_page()

            try:
                print("LOG: 步骤 1 - 直接导航到搜索结果页...")
                params = {'q': keyword}
                search_url = f"https://www.goofish.com/search?{urlencode(params)}&spm=a21ybx.home.searchInput.0"
                print(f"   -> 目标URL: {search_url}")

                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector('text=新发布', timeout=15000)

                if await self.check_anti_spider_dialog(page):
                    raise ValidationError('反爬虫验证弹窗')

                try:
                    await page.click("div[class*='closeIconBg']", timeout=3000)
                    print("LOG: 已关闭广告弹窗。")
                except TimeoutError:
                    print("LOG: 未检测到广告弹窗。")

                print("\nLOG: 步骤 2 - 应用筛选条件...")

                await page.click('text=新发布')

                await random_sleep(0.5, 2)

                await page.click('text=最新')

                await random_sleep(3, 5)

                if personal_only:
                    await page.click('text=个人闲置')
                    await random_sleep(2, 4)

                if min_price or max_price:
                    price_container = page.locator('div[class*="search-price-input-container"]').first
                    if await price_container.is_visible():
                        if min_price:
                            await price_container.get_by_placeholder("¥").first.fill(min_price)
                            await random_sleep(1, 2.5)
                        if max_price:
                            await price_container.get_by_placeholder("¥").nth(1).fill(max_price)
                            await random_sleep(1, 2.5)

                        await page.keyboard.press('Tab')
                        await random_sleep(4, 7)

                    else:
                        print("LOG: 警告 - 未找到价格输入容器。")

                print("\nLOG: 所有筛选已完成")

                page_tiny = await page.locator('span[class*="search-page-tiny-page"]').first.text_content()

                o_max_page = self.get_max_page(page_tiny)

                max_page = min(o_max_page, max_pages)

                print(f"\nLOG: 共有 {o_max_page} 页，需处理 {max_page} 页")

                for page_num in range(1, max_pages + 1):
                    page_btn = await page.locator('div[class*="search-pagination-page-box"]').all()
                    async with page.expect_response(lambda r: API_URL_PATTERN in r.url, timeout=20000) as response_info:
                        try:
                            print(f"\n--- 正在处理第 {page_num}/{max_pages} 页 ---")
                            await page_btn[page_num - 1].click()
                            current_response = await response_info.value
                            data = await current_response.json()
                            await self.process_page(data)
                            print(f"\n--- 第 {page_num}/{max_pages} 页处理完成 ---")
                        except ValidationError as e:
                            raise e
                        except Exception as e:
                            print(e)
                            print(f'\n--- 第 {page_num}/{max_pages} 页处理失败 ---')

            except ValidationError as e:
                print("\n==================== CRITICAL BLOCK DETECTED ====================")
                print(f"检测到闲鱼反爬虫验证 ({e})，程序将终止。")
                long_sleep_duration = random.randint(300, 600)
                print(f"为避免账户风险，将执行一次长时间休眠 ({long_sleep_duration} 秒) 后再退出...")
                await asyncio.sleep(long_sleep_duration)
                print("长时间休眠结束，现在将安全退出。")
                print("===================================================================")
                print("触发闲鱼反爬虫机制，将关闭浏览器")
                await self.browser.close()
            except Exception as e:
                print(f'程序发生错误 {e}')
                await self.browser.close()

        return len(self.processed_ids) - last_processed_count


async def main(debug: bool = False):
    parser = argparse.ArgumentParser(
        description="闲鱼商品监控脚本，支持多任务配置和实时AI分析。",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--debug", type=bool, default=False, help="调试模式：每个任务仅处理每页前 2 个新商品")
    parser.add_argument("--tasks", type=str, default="tasks.json", help="指定任务配置文件路径（默认为 tasks.json）")
    parser.add_argument("--task-id", type=int, help="运行指定id的单个任务 (用于定时任务调度)")

    args = parser.parse_args()

    if args.debug or debug:
        os.environ["DEBUG"] = "1"

    if not os.path.exists(STATE_FILE):
        sys.exit(f"错误: 登录状态文件 '{STATE_FILE}' 不存在。请先运行 login.py 生成。")

    if not os.path.exists(args.tasks):
        sys.exit(f"错误: 任务文件 '{args.tasks}' 不存在。")

    tasks = []

    try:
        with open(args.tasks, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        sys.exit(f"错误: 读取或解析配置文件 '{args.tasks}' 失败: {e}")

    active_tasks = []

    if args.task_id:
        task = next((it for it in tasks if it['task_id'] == args.task_id), None)
        if not task:
            print(f"错误：在配置文件中未找到id为 '{args.task_id}' 的任务。")
            sys.exit(f"错误: 任务 '{args.task_id}' 不存在。")

        active_tasks.append(task)

    else:
        active_tasks = [task for task in tasks if task.get('enabled', False)]

    if not active_tasks:
        print("没有需要执行的任务，程序退出。")
        return

    notification_manager = NotificationManager()
    coroutines = []
    for task in active_tasks:
        print(f"-> 任务 '{task['task_name']}' 已加入执行队列。")
        spider = GoofishSpider(task, notification_manager)
        coroutines.append(spider.run())

    results = await asyncio.gather(*coroutines, return_exceptions=True)

    print("\n--- 所有任务执行完毕 ---")

    for i, result in enumerate(results):
        task_name = active_tasks[i]['task_name']
        if isinstance(result, Exception):
            print(f"任务 '{task_name}' 因异常而终止: {result}")
        else:
            print(f"任务 '{task_name}' 正常结束，本次运行共处理了 {result} 个新商品。")


if __name__ == "__main__":
    asyncio.run(main())
