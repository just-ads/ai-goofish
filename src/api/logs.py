from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import verify_token
from src.api.utils import success_response
from src.task.logs import get_task_logs
from src.utils.logger import logger

router = APIRouter(prefix='/logs', tags=['logs'])


class LogsRequest(BaseModel):
    from_time: Optional[str] = None
    limit: Optional[int] = None
    levels: Optional[List[str]] = None


@router.post("/{task_id}", dependencies=[Depends(verify_token)])
async def api_get_task_logs(task_id: int, data: LogsRequest):
    """获取任务日志"""
    try:
        from_time = datetime.fromisoformat(data.from_time) if data.from_time else None
        logs = await get_task_logs(task_id, from_time, data.limit, data.levels)
        return success_response("任务日志获取成功", logs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务日志失败: {e}")
        raise HTTPException(status_code=500, detail="获取任务日志失败")

# @router.websocket()
