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
from src.utils.logger import logger

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
        logger.debug(f"终止进程: 任务 {task_id} 无进程PID")
        return was_running

    logger.info(f"正在终止任务 {task_id} 的进程 (PID: {pid})")

    try:
        if sys.platform == "win32":
            try:
                os.kill(pid, signal.CTRL_BREAK_EVENT)
                logger.debug(f"Windows: 发送 CTRL_BREAK_EVENT 到 PID {pid}")
            except Exception as e:
                logger.warning(f"CTRL_BREAK_EVENT 失败: {e}, 尝试 taskkill")
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               check=True)
        else:
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
                logger.debug(f"Unix: 发送 SIGTERM 到进程组 {pgid}")
            except Exception as e:
                logger.warning(f"终止进程组失败: {e}, 尝试终止单个进程")
                os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        logger.debug(f"进程 {pid} 已不存在")
    except Exception as e:
        logger.error(f"终止进程 {pid} 时发生错误: {e}")
    finally:
        running_tasks.pop(task_id, None)
        scraper_processes.pop(task_id, None)
        logger.info(f"任务 {task_id} 已停止")

    return was_running


async def initialize_task_scheduler():
    """初始化并启动任务调度器，加载所有启用的任务"""
    logger.info("正在加载定时任务调度器...")

    try:
        tasks = await get_all_tasks()
        enabled_tasks = [t for t in tasks if t.get('enabled')]

        logger.info(f"找到 {len(tasks)} 个任务，其中 {len(enabled_tasks)} 个已启用")

        for task in enabled_tasks:
            add_task_to_scheduler(task)

        logger.info("所有任务已添加到调度器")

        if not scheduler.running:
            scheduler.start()
            logger.info("调度器已启动")
        else:
            logger.warning("调度器已在运行状态")

    except Exception as e:
        logger.error(f"初始化任务调度器失败: {e}")
        raise


def shutdown_task_scheduler():
    """关闭任务调度器并终止所有正在执行的任务"""
    logger.info("正在停止所有定时任务...")

    try:
        scheduler.remove_all_jobs()
        logger.debug("已移除所有调度器作业")

        if scheduler.running:
            scheduler.shutdown()
            logger.info("调度器已关闭")

        task_ids = list(set(list(running_tasks.keys()) + list(scraper_processes.keys())))
        logger.info(f"正在终止 {len(task_ids)} 个运行中的任务")

        for task_id in task_ids:
            terminate_process(task_id)

        logger.info("所有定时任务已停止")

    except Exception as e:
        logger.error(f"关闭任务调度器时发生错误: {e}")
        raise


def is_task_running(task_id: int) -> bool:
    if running_tasks.get(task_id, False):
        logger.debug(f"任务 {task_id} 在运行状态缓存中标记为运行中")
        return True
    pid = scraper_processes.get(task_id)
    is_alive = _is_process_alive(pid)
    if is_alive:
        logger.debug(f"任务 {task_id} 的进程 (PID: {pid}) 存活")
    return is_alive


def get_all_running_tasks() -> dict[int, bool]:
    logger.debug(f"获取所有运行中任务: 当前 {len(running_tasks)} 个")
    return running_tasks.copy()


async def run_task(task_id: int, task_name: str):
    logger.info(f"定时任务触发: 正在为任务 '{task_name}' (ID: {task_id}) 启动爬虫...")

    if is_task_running(task_id):
        logger.warning(f"任务 '{task_name}' (ID: {task_id}) 已在运行中，跳过此次执行")
        return

    try:
        async with semaphore:
            logger.debug(f"获取信号量: 任务 {task_id} 开始执行")
            running_tasks[task_id] = True

            logger.info(f"启动子进程执行爬虫: 任务ID={task_id}")
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-u", "start_spider.py", "--task-id", str(task_id),
                start_new_session=True
            )

            scraper_processes[task_id] = process.pid
            logger.info(f"爬虫子进程已启动: PID={process.pid}, 任务ID={task_id}")

            return_code = await process.wait()

            if return_code == 0:
                logger.info(f"任务 '{task_name}' (ID: {task_id}) 执行成功，退出码: {return_code}")
            else:
                logger.warning(f"任务 '{task_name}' (ID: {task_id}) 执行异常，退出码: {return_code}")

    except asyncio.CancelledError:
        logger.warning(f"任务 '{task_name}' (ID: {task_id}) 被取消")
        raise
    except Exception as e:
        logger.error(f"执行任务 '{task_name}' (ID: {task_id}) 时发生错误: {e}")
        raise
    finally:
        running_tasks.pop(task_id, None)
        scraper_processes.pop(task_id, None)
        logger.debug(f"任务 {task_id} 执行完成，清理状态")


def stop_task(task_id: int):
    """停止正在运行的指定任务"""
    logger.info(f"手动停止任务 {task_id}")
    was_running = terminate_process(task_id)

    if was_running:
        logger.info(f"任务 {task_id} 已成功停止")
    else:
        logger.warning(f"任务 {task_id} 原本未在运行状态")


def remove_task_from_scheduler(task_id: int):
    """从调度器中移除任务并终止"""
    logger.info(f"从调度器中移除任务 {task_id}")

    job_id = f'task_{task_id}'
    try:
        scheduler.remove_job(job_id)
        logger.debug(f"已从调度器移除作业 {job_id}")
    except JobLookupError:
        logger.warning(f"作业 {job_id} 不存在于调度器中")
    finally:
        was_running = terminate_process(task_id)
        if was_running:
            logger.info(f"任务 {task_id} 已从调度器移除并停止运行")
        else:
            logger.info(f"任务 {task_id} 已从调度器移除")


def add_task_to_scheduler(task: Task):
    task_id = task.get('task_id')
    task_name = task.get('task_name')
    cron_str = task.get('cron')
    is_enabled = task.get('enabled', False)

    if not (is_enabled and cron_str):
        logger.warning(f"任务 '{task_name}' (ID: {task_id}) 未启用或无cron配置，跳过调度")
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

    logger.info(f"已为任务 '{task_name}' (ID: {task_id}) 添加定时规则: '{cron_str}'")


async def update_scheduled_task(task: Task):
    task_id = task.get('task_id')
    task_name = task.get('task_name')
    logger.info(f"更新调度任务: 任务ID={task_id}, 名称='{task_name}'")

    job_id = f'task_{task_id}'
    was_running = is_task_running(task_id)

    if was_running:
        logger.info(f"任务 {task_id} 正在运行，先停止")

    was_terminated = terminate_process(task_id)

    try:
        scheduler.remove_job(job_id)
        logger.debug(f"已移除旧任务 {job_id}")
    except JobLookupError:
        logger.debug(f"任务 {job_id} 不存在，无需移除")

    add_task_to_scheduler(task)

    if was_terminated:
        logger.info(f"更新任务: 重新启动任务 {task_id}")
        await run_task(task_id, task_name)
    else:
        logger.info(f"更新任务: 任务 {task_id} 已更新调度配置")
