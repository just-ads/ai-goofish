"""
Notifier相关路由模块
处理Notifier配置的增删改查、测试等功能
"""
from fastapi import APIRouter, HTTPException, Depends

from src.api.auth import verify_token, success_response
from src.notify.config import (
    get_notifier_config, get_all_notifiers,
    add_notifier_config, update_notifier_config,
    remove_notifier_config
)
from src.notify.notify_manger import NotificationManager
from src.notify.template import get_notifier_template

# 创建路由器
router = APIRouter(prefix="/notifier", tags=["notifier"])


# --------------- Notifier模板接口 ----------------
@router.get("/templates", dependencies=[Depends(verify_token)])
async def api_get_notifier_templates():
    """获取Notifier预设模板列表"""
    try:
        templates = get_notifier_template()
        return success_response('获取成功', templates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")


# --------------- Notifier配置管理接口 ----------------
@router.get("", dependencies=[Depends(verify_token)])
async def api_get_notifiers():
    """获取所有Notifier配置"""
    try:
        notifiers = await get_all_notifiers()
        # 转换为字典列表
        for notifier in notifiers:
            # 隐藏敏感信息
            if 'token' in notifier and notifier['token']:
                notifier['token'] = '***' + notifier['token'][-4:] if len(notifier['token']) > 4 else '***'

        return success_response("获取成功", notifiers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Notifier配置失败: {str(e)}")


@router.post("", dependencies=[Depends(verify_token)])
async def api_create_notifier(config: dict):
    """创建Notifier配置"""
    try:
        result = await add_notifier_config(config)
        if not result:
            raise HTTPException(status_code=500, detail="保存Notifier配置失败")

        if 'token' in result and result['token']:
            result['token'] = '***' + result['token'][-4:] if len(result['token']) > 4 else '***'

        return success_response("创建成功", result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建Notifier配置失败: {str(e)}")


@router.get("/{notifier_id}", dependencies=[Depends(verify_token)])
async def api_get_notifier(notifier_id: str):
    """获取单个Notifier配置"""
    try:
        notifier = await get_notifier_config(notifier_id)
        if not notifier:
            raise HTTPException(status_code=404, detail=f"Notifier '{notifier_id}' 未找到")

        if 'token' in notifier and notifier['token']:
            notifier['token'] = '***' + notifier['token'][-4:] if len(notifier['token']) > 4 else '***'

        return success_response("获取成功", notifier)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Notifier配置失败: {str(e)}")


@router.post("/test", dependencies=[Depends(verify_token)])
async def api_notifier_test(config: dict):
    """测试Notifier配置（创建测试）"""
    try:
        notifier = NotificationManager.create_notifier(config)
        if not notifier:
            raise HTTPException(status_code=500, detail=f"测试失败，无效配置")

        notifier.test()
        return success_response('测试成功')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试Notifier失败: {str(e)}")


@router.post("/{notifier_id}", dependencies=[Depends(verify_token)])
async def api_update_notifier(notifier_id: str, config: dict):
    """更新Notifier配置"""
    try:
        # 更新配置
        notifier = await update_notifier_config(notifier_id, config)
        if not notifier:
            raise HTTPException(status_code=500, detail="更新Notifier配置失败")

        if 'token' in notifier and notifier['token']:
            notifier['token'] = '***' + notifier['token'][-4:] if len(notifier['token']) > 4 else '***'

        return success_response("更新成功", notifier)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新Notifier配置失败: {str(e)}")


@router.delete("/{notifier_id}", dependencies=[Depends(verify_token)])
async def api_delete_notifier(notifier_id: str):
    """删除Notifier配置"""
    try:
        existing_notifier = await get_notifier_config(notifier_id)
        if not existing_notifier:
            raise HTTPException(status_code=404, detail=f"Notifier '{notifier_id}' 未找到")

        result = await remove_notifier_config(notifier_id)
        if not result:
            raise HTTPException(status_code=500, detail="删除Notifier配置失败")

        return success_response("删除成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除Notifier配置失败: {str(e)}")


# --------------- Notifier操作接口 ----------------
@router.post("/{notifier_id}/test", dependencies=[Depends(verify_token)])
async def api_test_notifier(notifier_id: str):
    """测试已保存的Notifier连接"""
    try:
        # 获取notifier配置
        notifier_config = await get_notifier_config(notifier_id)
        if not notifier_config:
            raise HTTPException(status_code=404, detail=f"Notifier '{notifier_id}' 未找到")

        # 创建notifier实例
        notifier = NotificationManager.create_notifier(notifier_config)
        if not notifier:
            raise HTTPException(status_code=500, detail="创建Notifier实例失败")

        # 测试连接
        notifier.test()

        return success_response('测试成功')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试Notifier失败: {str(e)}")
