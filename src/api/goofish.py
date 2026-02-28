"""
Goofish状态相关路由模块
处理Goofish状态的保存、删除、查询等操作
"""
import json
import os
from fastapi import APIRouter, HTTPException, Depends

from src.account.login import start_login, check_login, login, send_sms_code, close_login_session
from src.account.verify import verify_login
from src.api.auth import verify_token
from src.api.utils import success_response
from src.types import (
    GoofishState,
    GoofishStartLoginRequest,
    GoofishSessionRequest,
    GoofishSmsCodeRequest,
    GoofishLoginRequest,
)
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
    return success_response("状态获取成功", await verify_login())


@router.post('/start_login', dependencies=[Depends(verify_token)])
async def api_start_login(req: GoofishStartLoginRequest):
    """开始闲鱼登录流程并返回二维码"""
    try:
        data = await start_login(timeout_seconds=req.timeout_seconds or 180)
        return success_response("登录流程已启动", data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/check_login', dependencies=[Depends(verify_token)])
async def api_check_login(req: GoofishSessionRequest):
    """轮询登录状态"""
    try:
        data = await check_login(req.session_id)
        return success_response("状态获取成功", data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/send_sms_code', dependencies=[Depends(verify_token)])
async def api_send_sms_code(req: GoofishSmsCodeRequest):
    """短信登录发送验证码"""
    try:
        data = await send_sms_code(req.model_dump())
        return success_response("验证码已发送", data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/login', dependencies=[Depends(verify_token)])
async def api_goofish_login(req: GoofishLoginRequest):
    """提交闲鱼登录信息"""
    try:
        data = await login(req.model_dump())
        return success_response("登录请求已提交", data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/close_login_session', dependencies=[Depends(verify_token)])
async def api_close_login_session(req: GoofishSessionRequest):
    """主动关闭登录会话，释放浏览器资源"""
    try:
        closed = await close_login_session(req.session_id)
        return success_response("登录会话已关闭", {"closed": closed})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
