import asyncio
import os
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.task.task import get_all_tasks

# scraper_processes = {}
running_tasks = {}
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def run_task(task_id: int, task_name: str):
    print(f"定时任务触发: 正在为任务 '{task_name}' 启动爬虫...")
    try:
        running_tasks.setdefault(1, True)
        # preexec_fn = os.setsid if sys.platform != "win32" else None
        # process = await asyncio.create_subprocess_exec(
        #     sys.executable, "-u", "spider_v2.py", "--task-name", task_name,
        #     preexec_fn=preexec_fn
        # )
        # # 等待进程结束
        # await process.wait()
    except Exception as e:
        running_tasks[task_id] = False


async def load_jobs():
    print("正在加载定时任务调度器...")
    try:
        tasks = await get_all_tasks()
        for i, task in tasks:
            task_name = task.get('task_name')
            cron_str = task.get('cron')
            is_enabled = task.get('enabled', False)

            if all([is_enabled, cron_str]):
                try:
                    trigger = CronTrigger.from_crontab(cron_str)
                    scheduler.add_job(
                        run_task,
                        trigger=trigger,
                        args=[i, task_name],
                        id=f"task_{i}",
                        name=f"Scheduled: {task_name}",
                        replace_existing=True
                    )
                    print(f"  -> 已为任务 '{task_name}' 添加定时规则: '{cron_str}'")
                except ValueError as e:
                    print(f"  -> [警告] 任务 '{task_name}' 的 Cron 表达式 '{cron_str}' 无效，已跳过: {e}")

    except Exception as e:
        print(e)
