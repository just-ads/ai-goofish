import asyncio
import os
import signal
import subprocess
import sys
from typing import Optional

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.env import MAX_CONCURRENT_TASKS
from src.task.logs import get_logs_file_name, trim_log_file
from src.task.task import get_tasks, Task
from src.utils.date import now_str
from src.utils.logger import logger

# 任务进程表与运行状态缓存
scraper_processes: dict[int, int] = {}
running_tasks: dict[int, bool] = {}
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

# 并发限制（同时运行的任务数）
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

MAX_LOG_SIZE = 512 * 1024  # 512K


# ==================== Unix 僵尸进程收割机制 ====================
# Windows 无僵尸进程概念，以下函数仅在 Unix 上生效

def _setup_zombie_reaper():
    """初始化僵尸进程收割机制（仅 Unix）

    在 Unix 上设置:
    1. SIGCHLD 信号处理器 - 即时收割退出的子进程
    2. zombie_reaper 协程 - 定时轮询兜底收割

    Windows 上此函数为空操作。
    """
    if sys.platform == "win32":
        return

    # 设置 SIGCHLD 信号处理器
    def sigchld_handler(signum, frame):
        """SIGCHLD 信号处理器：立即收割已退出的子进程"""
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
                logger.debug(f"SIGCHLD: 已收割进程 PID {pid}, 退出状态 {status}")
            except ChildProcessError:
                break
            except Exception:
                break

    signal.signal(signal.SIGCHLD, sigchld_handler)
    logger.info("已安装 SIGCHLD 信号处理器")

    # 启动定时收割协程
    asyncio.create_task(_zombie_reaper_loop())
    logger.info("已启动僵尸进程收割协程")


async def _zombie_reaper_loop():
    """定期清理僵尸进程的后台任务（仅 Unix 内部使用）"""
    while True:
        try:
            while True:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
                logger.debug(f"已收割僵尸进程: PID {pid}, 退出状态 {status}")
        except ChildProcessError:
            pass
        except Exception as e:
            logger.error(f"收割僵尸进程时出错: {e}")

        await asyncio.sleep(30)


# ==================== 进程管理工具函数 ====================

def _is_process_alive(pid: Optional[int]) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _wait_for_process_exit(pid: int, timeout: float = 3.0) -> bool:
    """等待进程退出并收割，返回是否成功收割。仅 Unix 有效。"""
    if sys.platform == "win32":
        return True  # Windows 无僵尸进程问题

    import time
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            wpid, status = os.waitpid(pid, os.WNOHANG)
            if wpid == pid:
                logger.debug(f"进程 {pid} 已收割，退出状态: {status}")
                return True
            if wpid == 0:
                # 进程还在运行，短暂等待后重试
                time.sleep(0.1)
                continue
        except ChildProcessError:
            # 不是我们的子进程或已被收割
            logger.debug(f"进程 {pid} 不是子进程或已被收割")
            return True
        except Exception as e:
            logger.warning(f"waitpid({pid}) 出错: {e}")
            return False
    return False


def terminate_process(task_id: int) -> bool:
    """终止指定 task_id 的子进程；返回值表示**此前**该任务是否处于运行状态。"""
    pid = scraper_processes.get(task_id)
    if pid is None:
        logger.debug(f"终止进程: 任务 {task_id} 无进程PID记录")
        was_running = running_tasks.get(task_id, False)
        running_tasks.pop(task_id, None)
        return was_running

    was_running = running_tasks.get(task_id, False) or _is_process_alive(pid)

    if not pid:
        running_tasks.pop(task_id, None)
        scraper_processes.pop(task_id, None)
        logger.debug(f"终止进程: 任务 {task_id} 无进程PID")
        return was_running

    logger.info(f"正在终止任务 {task_id} 的进程 (PID: {pid})")

    try:
        if sys.platform == "win32":
            # Windows: 使用 taskkill 终止进程树，无僵尸进程问题
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
                logger.debug(f"Windows: 使用 taskkill 终止进程 {pid}")
            except subprocess.TimeoutExpired:
                logger.warning(f"taskkill 超时")
            except Exception as e:
                logger.warning(f"taskkill 失败: {e}")
        else:
            # Unix: 终止进程并收割
            try:
                os.kill(pid, signal.SIGTERM)
                logger.debug(f"Unix: 发送 SIGTERM 到进程 {pid}")

                # 等待进程退出并收割
                if not _wait_for_process_exit(pid, timeout=2.0):
                    # 超时未退出，发送 SIGKILL
                    logger.warning(f"进程 {pid} 未响应 SIGTERM，发送 SIGKILL")
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    # 再次等待收割
                    _wait_for_process_exit(pid, timeout=1.0)

            except ProcessLookupError:
                logger.debug(f"进程 {pid} 已不存在")
            except Exception as e:
                logger.warning(f"终止进程失败: {e}")
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
        tasks = await get_tasks()
        enabled_tasks = [t for t in tasks if t.get('enabled')]

        if not scheduler.running:
            scheduler.start()
            _setup_zombie_reaper()  # 初始化僵尸进程收割机制（仅 Unix 生效）
            logger.info("调度器已启动")
        else:
            logger.warning("调度器已在运行状态")

        logger.info(f"找到 {len(tasks)} 个任务，其中 {len(enabled_tasks)} 个已启用")

        for task in enabled_tasks:
            add_task_to_scheduler(task)

        logger.info("所有任务已添加到调度器")

    except Exception as e:
        logger.error(f"初始化任务调度器失败: {e}")
        raise


def shutdown_task_scheduler():
    """关闭任务调度器并终止所有正在执行的任务"""
    logger.info("正在停止所有定时任务...")

    try:
        scheduler.remove_all_jobs()
        logger.debug("已移除所有调度器任务")

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
    if pid is None:
        logger.debug(f"任务 {task_id} 无PID记录，认为未运行")
        return False
    is_alive = _is_process_alive(pid)
    if is_alive:
        logger.debug(f"任务 {task_id} 的进程 (PID: {pid}) 存活")
    else:
        logger.debug(f"任务 {task_id} 的进程 (PID: {pid}) 未存活，清理记录")
        scraper_processes.pop(task_id, None)
    return is_alive


def get_all_running_tasks() -> dict[int, bool]:
    logger.debug(f"获取所有运行中任务: 当前 {len(running_tasks)} 个")
    return running_tasks.copy()


async def run_task(task_id: int, task_name: str):
    start_time = asyncio.get_event_loop().time()
    logger.info(f"定时任务触发: 正在为任务 '{task_name}' (ID: {task_id}) 启动爬虫...")
    logger.info(f"任务执行开始时间: {now_str()}")

    if is_task_running(task_id):
        logger.warning(f"任务 '{task_name}' (ID: {task_id}) 已在运行中，跳过此次执行")
        logger.info(f"跳过执行原因: 任务已在运行状态，PID={scraper_processes.get(task_id)}")
        return

    running_tasks[task_id] = True

    try:
        async with semaphore:
            logger.debug(f"获取信号量: 任务 {task_id} 开始执行")

            if not running_tasks[task_id]:
                logger.warning(f"任务 '{task_name}' (ID: {task_id}) 已取消, 中断执行")
                return

            logger.info(f"当前并发任务数: {MAX_CONCURRENT_TASKS - semaphore._value}/{MAX_CONCURRENT_TASKS}")
            logger.info(f"启动子进程执行爬虫: 任务ID={task_id}")
            logs_file = get_logs_file_name(task_id)
            logger.debug(f"日志文件路径: {logs_file}")
            trim_log_file(logs_file, MAX_LOG_SIZE)

            with open(logs_file, 'a') as f:
                process = await asyncio.create_subprocess_exec(
                    sys.executable, "-u", "start_spider.py", "--task-id", str(task_id),
                    stdout=f.fileno(),
                    stderr=asyncio.subprocess.STDOUT
                )

            scraper_processes[task_id] = process.pid
            logger.info(f"爬虫子进程已启动: PID={process.pid}, 任务ID={task_id}")
            logger.info(f"子进程命令: {sys.executable} -u start_spider.py --task-id {task_id}")

            return_code = await process.wait()
            execution_time = asyncio.get_event_loop().time() - start_time

            if return_code == 0:
                logger.info(f"任务 '{task_name}' (ID: {task_id}) 执行成功，退出码: {return_code}, 执行耗时: {execution_time:.2f}秒")
            else:
                logger.warning(f"任务 '{task_name}' (ID: {task_id}) 执行异常，退出码: {return_code}, 执行耗时: {execution_time:.2f}秒")

    except asyncio.CancelledError:
        execution_time = asyncio.get_event_loop().time() - start_time
        logger.warning(f"任务 '{task_name}' (ID: {task_id}) 被取消，执行耗时: {execution_time:.2f}秒")
        if task_id in scraper_processes:
            terminate_process(task_id)
        raise
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"执行任务 '{task_name}' (ID: {task_id}) 时发生错误: {e}, 执行耗时: {execution_time:.2f}秒")
        logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
        raise
    finally:
        running_tasks.pop(task_id, None)
        scraper_processes.pop(task_id, None)
        logger.info(f"任务 {task_id} 执行完成，状态已清理，总耗时: {(asyncio.get_event_loop().time() - start_time):.2f}秒")


def get_scheduler_status():
    return {
        'running': scheduler.running,
        'jobs': len(scheduler.get_jobs()),
        'concurrency': semaphore._value,
        'max_concurrency': MAX_CONCURRENT_TASKS,
    }


def get_task_status(task_id: int):
    """获取任务状态"""
    job = scheduler.get_job(f"task_{task_id}")
    next_run_time = job.next_run_time if job else None
    next_run_time = next_run_time.strftime("%Y-%m-%d %H:%M") if next_run_time else None
    return {
        'running': is_task_running(task_id),
        'next_run_time': next_run_time
    }


def stop_task(task_id: int):
    """停止正在运行的指定任务"""
    logger.info(f"手动停止任务 {task_id}")
    was_running = terminate_process(task_id)

    if was_running:
        logger.info(f"任务 {task_id} 已成功停止")
        logs_file = get_logs_file_name(task_id)
        logger.warning_file(logs_file, f"任务已被手动中止")
    else:
        logger.warning(f"任务 {task_id} 原本未在运行状态")


def remove_task_from_scheduler(task_id: int):
    """从调度器中移除任务并终止"""
    logger.info(f"从调度器中移除任务 {task_id}")

    job_id = f'task_{task_id}'
    try:
        scheduler.remove_job(job_id)
        logger.debug(f"已从调度器移除任务 {job_id}")
    except JobLookupError:
        logger.warning(f"任务 {job_id} 不存在于调度器中")
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

    if task_id is None:
        logger.error("添加任务失败: task_id 为 None")
        return

    if not (is_enabled and cron_str):
        logger.warning(f"任务 '{task_name}' (ID: {task_id}) 未启用或无cron配置，跳过调度")
        logger.debug(f"任务状态: enabled={is_enabled}, cron='{cron_str}'")
        return

    trigger = CronTrigger.from_crontab(cron_str, timezone='Asia/Shanghai')

    trigger.jitter = 30

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
    logger.info(f"触发器配置: {cron_str}, 随机偏移=30秒")

    job = scheduler.get_job(f"task_{task_id}")
    if job:
        logger.info(f"任务 '{task_name}' 下次执行时间: {job.next_run_time}")
    else:
        logger.error(f"无法获取任务 '{task_name}' 的调度信息")


async def update_scheduled_task(task: Task):
    task_id = task.get('task_id')
    task_name = task.get('task_name')

    if task_id is None:
        logger.error("更新任务失败: task_id 为 None")
        return

    logger.info(f"更新调度任务: 任务ID={task_id}, 名称='{task_name}'")
    logger.debug(f"任务配置: {task}")

    job_id = f'task_{task_id}'
    was_running = is_task_running(task_id)

    # 先停止正在运行的任务
    if was_running:
        logger.info(f"任务 {task_id} 正在运行，先停止")
        terminate_process(task_id)
        # 等待一小段时间确保进程完全停止
        await asyncio.sleep(0.5)
        logger.info(f"任务 {task_id} 已停止")

    # 更新调度器中的任务
    try:
        scheduler.remove_job(job_id)
        logger.debug(f"已移除旧任务 {job_id}")
    except JobLookupError:
        logger.debug(f"任务 {job_id} 不存在，无需移除")

    add_task_to_scheduler(task)

    logger.info(f"更新任务: 任务 {task_id} 已更新调度配置")

    # 验证更新结果
    updated_job = scheduler.get_job(job_id)
    if updated_job:
        logger.info(f"更新验证: 任务 {task_id} 下次执行时间: {updated_job.next_run_time}")
    else:
        logger.error(f"更新验证失败: 无法找到任务 {task_id}")
