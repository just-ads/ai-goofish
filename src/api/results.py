"""
结果相关路由模块
处理任务结果的查询、删除等操作
"""
from fastapi import APIRouter, HTTPException, Depends

from src.api.auth import verify_token
from src.api.utils import success_response
from src.task.result import get_task_result, remove_task_result, get_product_history_info
from src.task.task import get_task
from src.types import PaginationOptions

# 创建路由器
router = APIRouter(prefix="/results", tags=["results"])

# --------------- 结果相关接口 ----------------
@router.post("/{task_id}", dependencies=[Depends(verify_token)])
async def api_get_task_results(task_id: int, data: PaginationOptions):
    """获取任务结果"""
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")

        keyword = task.get('keyword')
        if not keyword:
            raise HTTPException(status_code=400, detail="任务缺少关键词")

        # 提供默认值
        page = data.page if data.page is not None else 1
        limit = data.limit if data.limit is not None else 20
        recommended_only = data.recommended_only if data.recommended_only is not None else False

        result = await get_task_result(
            keyword=keyword,
            page=page,
            limit=limit,
            recommended_only=recommended_only,
            sort_by=data.sort_by,
            order=data.order
        )
        return success_response("结果获取成功", result)
    except Exception:
        raise HTTPException(status_code=500, detail="结果获取失败")


@router.delete("/{task_id}", dependencies=[Depends(verify_token)])
async def api_remove_task_results(task_id: int):
    """删除任务结果"""
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")

        keyword = task.get('keyword')
        if not keyword:
            raise HTTPException(status_code=400, detail="任务缺少关键词")

        remove_task_result(keyword)
        return success_response("删除成功")
    except Exception:
        raise HTTPException(status_code=500, detail="删除失败")


@router.get('/prices/{task_id}', dependencies=[Depends(verify_token)])
async def api_get_task_prices(task_id: int):
    """获取任务价格历史"""
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")

        keyword = task.get('keyword')
        if not keyword:
            raise HTTPException(status_code=400, detail="任务缺少关键词")

        history_info = await get_product_history_info(keyword)
        return success_response('获取成功', history_info.get('prices'))
    except Exception:
        raise HTTPException(status_code=500, detail="获取失败")