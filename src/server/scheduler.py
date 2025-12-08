import asyncio
import os
import signal
import subprocess
import sys
from typing import Optional

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import MAX_CONCURRENT_TASKS
from src.server.trigger import RandomOffsetTrigger
from src.task.task import get_all_tasks, Task

# 任务进程表与运行状态缓存
scraper_processes: dict[int, int] = {}
running_tasks: dict[int, bool] = {}
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

# 并发限制（同时运行的任务数）
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)


def _is_process_alive(pid: Optional[int]) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def terminate_process(task_id: int) -> bool:
    """终止指定 task_id 的子进程；返回值表示**此前**该任务是否处于运行状态。"""
    pid = scraper_processes.get(task_id)
    was_running = running_tasks.get(task_id, False) or _is_process_alive(pid)

    if not pid:
        running_tasks.pop(task_id, None)
        scraper_processes.pop(task_id, None)
        return was_running

    try:
        if sys.platform == "win32":
            try:
                os.kill(pid, signal.CTRL_BREAK_EVENT)
            except Exception:
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               check=True)
        else:
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
            except Exception:
                os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    finally:
        running_tasks.pop(task_id, None)
        scraper_processes.pop(task_id, None)

    return was_running


async def initialize_task_scheduler():
    """初始化并启动任务调度器，加载所有启用的任务"""
    print("正在加载定时任务调度器...")
    tasks = await get_all_tasks()
    enabled_tasks = [t for t in tasks if t.get('enabled')]
    for task in enabled_tasks:
        add_task_to_scheduler(task)
    print("所有任务已添加")

    if not scheduler.running:
        scheduler.start()
    print("调度器已启动")


def shutdown_task_scheduler():
    """关闭任务调度器并终止所有正在执行的任务"""
    print("正在停止所有定时任务...")
    scheduler.remove_all_jobs()
    if scheduler.running:
        scheduler.shutdown()

    for task_id in list(set(list(running_tasks.keys()) + list(scraper_processes.keys()))):
        terminate_process(task_id)

    print("所有定时任务已停止")


def is_task_running(task_id: int) -> bool:
    if running_tasks.get(task_id, False):
        return True
    pid = scraper_processes.get(task_id)
    return _is_process_alive(pid)


def get_all_running_tasks() -> dict[int, bool]:
    return running_tasks.copy()


async def run_task(task_id: int, task_name: str):
    print(f"定时任务触发: 正在为任务 '{task_name}' 启动爬虫...")

    if is_task_running(task_id):
        print(f"任务 '{task_name}' 已在运行中，跳过此次执行")
        return

    try:
        async with semaphore:
            running_tasks[task_id] = True

            process = await asyncio.create_subprocess_exec(
                sys.executable, "-u", "start_spider.py", "--task-id", str(task_id),
                start_new_session=True
            )

            scraper_processes[task_id] = process.pid
            return_code = await process.wait()

            print(f"任务 '{task_name}' 执行完成，退出码: {return_code}")
    finally:
        running_tasks.pop(task_id, None)
        scraper_processes.pop(task_id, None)


def stop_task(task_id: int):
    """停止正在运行的指定任务"""
    terminate_process(task_id)
    print(f"任务 {task_id} 已停止运行")


def remove_task_from_scheduler(task_id: int):
    """从调度器中移除任务并终止"""
    job_id = f'task_{task_id}'
    try:
        scheduler.remove_job(job_id)
    except JobLookupError:
        pass
    finally:
        terminate_process(task_id)

    print(f"任务 {task_id} 已移除调度器并停止运行")


def add_task_to_scheduler(task: Task):
    task_id = task.get('task_id')
    task_name = task.get('task_name')
    cron_str = task.get('cron')
    is_enabled = task.get('enabled', False)

    if not (is_enabled and cron_str):
        return

    # trigger = CronTrigger.from_crontab(cron_str)
    # 使用自定义随机触发器
    trigger = RandomOffsetTrigger(CronTrigger.from_crontab(cron_str), 1800)
    scheduler.add_job(
        run_task,
        trigger=trigger,
        args=[task_id, task_name],
        id=f"task_{task_id}",
        name=f"Scheduled: {task_name}",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=60
    )
    print(f"  -> 已为任务 '{task_name}' 添加定时规则: '{cron_str}'")


async def update_scheduled_task(task: Task):
    task_id = task.get('task_id')
    job_id = f'task_{task_id}'

    was_running = is_task_running(task_id)
    terminate_process(task_id)

    try:
        scheduler.remove_job(job_id)
    except JobLookupError:
        pass

    add_task_to_scheduler(task)

    if was_running:
        await run_task(task_id, task.get('task_name'))
        print(f"更新任务: 已重新启动任务 {task_id}")
