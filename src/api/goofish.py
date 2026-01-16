"""
Goofish状态相关路由模块
处理Goofish状态的保存、删除、查询等操作
"""
import json
import os
from fastapi import APIRouter, HTTPException, Depends

from src.api.auth import verify_token
from src.api.utils import success_response
from src.types import GoofishState
from src.env import STATE_FILE

# 创建路由器
router = APIRouter(prefix="/goofish", tags=["goofish"])

# --------------- Goofish状态相关接口 ----------------
@router.post("/state/save", dependencies=[Depends(verify_token)])
async def api_save_goofish_state(data: GoofishState):
    """保存Goofish状态"""
    try:
        # 验证JSON格式
        json.loads(data.content)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            f.write(data.content)
        return success_response("保存成功")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="提供的内容不是有效的JSON格式")
    except Exception:
        raise HTTPException(status_code=500, detail="保存失败")


@router.delete("/state/delete", dependencies=[Depends(verify_token)])
async def api_delete_goofish_state():
    """删除Goofish状态"""
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            return success_response("删除成功")
        else:
            raise HTTPException(status_code=404, detail="文件未找到")
    except Exception:
        raise HTTPException(status_code=500, detail="删除失败")


@router.get('/status', dependencies=[Depends(verify_token)])
async def api_get_goofish_status():
    """获取Goofish状态"""
    return success_response("状态获取成功", os.path.exists(STATE_FILE))