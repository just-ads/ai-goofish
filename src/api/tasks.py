"""
任务相关路由模块
处理任务的增删改查、启停等操作
"""
import asyncio
from typing import Optional

from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, HTTPException, Depends

from src.api.auth import verify_token
from src.api.utils import success_response
from src.server.scheduler import (
    add_task_to_scheduler,
    update_scheduled_task, run_task, remove_task_from_scheduler,
    is_task_running, get_all_running_tasks, stop_task, get_task_status
)
from src.task.record import get_task_record
from src.task.task import get_tasks, add_task, update_task, get_task, remove_task
from src.types import Task
from src.utils.logger import logger

# 创建路由器
router = APIRouter(prefix="/tasks", tags=["tasks"])


def _as_bool(value, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise HTTPException(status_code=400, detail=f"{field_name} 必须为布尔值")


def _as_positive_int(value, field_name: str) -> int:
    if isinstance(value, int):
        if value <= 0:
            raise HTTPException(status_code=400, detail=f"{field_name} 必须大于 0")
        return value
    if isinstance(value, str) and value.strip().isdigit():
        int_val = int(value.strip())
        if int_val <= 0:
            raise HTTPException(status_code=400, detail=f"{field_name} 必须大于 0")
        return int_val
    raise HTTPException(status_code=400, detail=f"{field_name} 必须为整数")


def _validate_task_payload(payload: Task, *, creating: bool, old_task: Optional[Task] = None) -> Task:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="请求体必须为 JSON 对象")

    merged = payload if creating else {**(old_task or {}), **payload}

    task_name = merged.get('task_name')
    if not isinstance(task_name, str) or not task_name.strip():
        raise HTTPException(status_code=400, detail="任务名称不能为空")

    keyword = merged.get('keyword')
    if not isinstance(keyword, str) or not keyword.strip():
        raise HTTPException(status_code=400, detail="搜索关键字不能为空")

    if 'max_pages' in merged:
        max_pages = _as_positive_int(merged.get('max_pages'), 'max_pages')
    else:
        if creating:
            raise HTTPException(status_code=400, detail="max_pages 不能为空")
        max_pages = None

    if max_pages is not None:
        payload['max_pages'] = max_pages

    enabled = merged.get('enabled', False)
    enabled = _as_bool(enabled, 'enabled')
    payload['enabled'] = enabled

    if enabled:
        cron_str = merged.get('cron')
        if not isinstance(cron_str, str) or not cron_str.strip():
            raise HTTPException(status_code=400, detail="启用任务时 cron 不能为空")
        try:
            CronTrigger.from_crontab(cron_str.strip(), timezone='Asia/Shanghai')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"cron 表达式无效: {e}")
        payload['cron'] = cron_str.strip()

    return payload


@router.get('/status', dependencies=[Depends(verify_token)])
async def api_get_tasks_status():
    """获取所有任务状态"""
    try:
        data = get_all_running_tasks()
        return success_response('请求成功', data)
    except Exception as e:
        logger.error(f"任务状态检测失败: {e}")
        raise HTTPException(status_code=500, detail="任务状态检测失败")


@router.get('/status/{task_id}', dependencies=[Depends(verify_token)])
async def api_get_task_status(task_id: int):
    """获取单个任务状态"""
    try:
        return success_response("任务状态检测", get_task_status(task_id))
    except Exception as e:
        logger.error(f"任务 {task_id} 状态检测失败: {e}")
        raise HTTPException(status_code=500, detail="任务状态检测失败")


# --------------- 任务相关接口 ----------------
@router.get("", dependencies=[Depends(verify_token)])
async def api_get_tasks():
    """获取所有任务"""
    try:
        tasks = await get_tasks()
        for task in tasks:
            task_id = task.get('task_id')
            if task_id is None:
                continue
            task_state = get_task_status(task_id)
            task.update(task_state)
            task_record = await get_task_record(task_id)
            task['run_record'] = task_record

        return success_response("任务获取成功", tasks)
    except Exception as e:
        logger.error(f"读取任务配置失败: {e}")
        raise HTTPException(status_code=500, detail="读取任务配置时发生错误")


@router.post("", dependencies=[Depends(verify_token)])
async def api_create_task(req: Task):
    """创建任务"""
    try:
        _validate_task_payload(req, creating=True)

        task = await add_task(req)

        if task.get('enabled'):
            add_task_to_scheduler(task)
        return success_response("任务创建成功", task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail="创建失败")


@router.get("/{task_id}", dependencies=[Depends(verify_token)])
async def api_get_task(task_id: int):
    """获取任务"""
    try:
        task = await get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 未找到")

        task_state = get_task_status(task_id)
        task.update(task_state)
        task_record = await get_task_record(task_id)
        task['run_record'] = task_record

        return success_response("任务获取成功", task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务 {task_id} 失败: {e}")
        raise HTTPException(status_code=500, detail="获取失败")


@router.post("/update", dependencies=[Depends(verify_token)])
async def api_update_task(req: Task):
    """更新任务"""
    try:
        task_id = req.get('task_id')
        if task_id is None:
            raise HTTPException(status_code=400, detail="任务ID不能为空")
        task_id_int: int = task_id

        old_task = await get_task(task_id_int)
        if not old_task:
            raise HTTPException(status_code=404, detail="任务未找到")

        _validate_task_payload(req, creating=False, old_task=old_task)

        new_task = await update_task(req)

        if new_task.get('enabled'):
            # 如果任务之前是禁用状态，现在启用了，添加到调度器
            if not old_task or not old_task.get('enabled'):
                add_task_to_scheduler(new_task)
                task_state = get_task_status(task_id_int)
                new_task.update(task_state)
            else:
                # 如果任务之前就是启用的，更新调度器中的任务
                await update_scheduled_task(new_task)
        else:
            # 如果任务被禁用，从调度器中移除
            remove_task_from_scheduler(task_id_int)

        return success_response("任务更新成功", new_task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        raise HTTPException(status_code=500, detail="更新任务失败")


@router.delete("/delete/{task_id}", dependencies=[Depends(verify_token)])
async def api_remove_task(task_id: int):
    """删除任务"""
    try:
        remove_task_from_scheduler(task_id)
        await remove_task(task_id)
        return success_response("任务删除成功")
    except Exception as e:
        logger.error(f"删除任务 {task_id} 失败: {e}")
        raise HTTPException(status_code=500, detail="更新删除失败")


@router.post("/run/{task_id}", dependencies=[Depends(verify_token)])
async def api_run_task(task_id: int):
    """运行任务"""
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")

        if is_task_running(task_id):
            return success_response("任务已在运行中", {"task_id": task_id, "running": True})

        task_id_val = task.get('task_id')
        task_name = task.get('task_name')
        if task_id_val is None or task_name is None:
            raise HTTPException(status_code=400, detail="任务信息不完整")

        asyncio.create_task(run_task(task_id_val, task_name))

        return success_response("任务启动中", {"task_id": task_id, "running": True})
    except Exception as e:
        logger.error(f"运行任务 {task_id} 失败: {e}")
        raise HTTPException(status_code=500, detail="任务运行失败")


@router.post('/stop/{task_id}', dependencies=[Depends(verify_token)])
async def api_stop_task(task_id: int):
    """停止任务"""
    try:
        stop_task(task_id)
        return success_response("任务停止成功")
    except Exception as e:
        logger.error(f"停止任务 {task_id} 失败: {e}")
        raise HTTPException(status_code=500, detail="任务停止失败")
