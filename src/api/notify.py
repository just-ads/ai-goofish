"""
Notifier相关路由模块
处理Notifier配置的增删改查、测试等功能
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from src.notify.notifier import NotifierConfig, NotifierPresetTemplate
from src.notify.notify_manger import NotificationManager
from src.notify.config import (
    get_notifier_config, get_all_notifiers,
    add_notifier_config, update_notifier_config,
    remove_notifier_config, NotifierCreateModel, NotifierUpdateModel
)
from src.api.auth import verify_token, success_response

# 创建路由器
router = APIRouter(prefix="/notifiers", tags=["notifiers"])


# --------------- Notifier模板接口 ----------------
@router.get("/templates", dependencies=[Depends(verify_token)])
async def api_get_notifier_templates():
    """获取Notifier预设模板列表"""
    try:
        templates = NotifierPresetTemplate.get_preset_templates()
        template_list = [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "type": template.type,
                "url": template.url,
                "token": template.token
            }
            for template in templates
        ]
        return success_response('获取成功', template_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")


# --------------- Notifier配置管理接口 ----------------
@router.get("", dependencies=[Depends(verify_token)])
async def api_get_notifiers():
    """获取所有Notifier配置"""
    try:
        notifiers = await get_all_notifiers()
        # 转换为字典列表
        notifier_list = []
        for notifier in notifiers:
            if notifier:
                notifier_dict = notifier.model_dump()
                # 隐藏敏感信息
                if 'token' in notifier_dict and notifier_dict['token']:
                    notifier_dict['token'] = '***' + notifier_dict['token'][-4:] if len(notifier_dict['token']) > 4 else '***'
                notifier_list.append(notifier_dict)

        return success_response("获取成功", notifier_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Notifier配置失败: {str(e)}")


@router.get("/{notifier_id}", dependencies=[Depends(verify_token)])
async def api_get_notifier(notifier_id: str):
    """获取单个Notifier配置"""
    try:
        notifier = await get_notifier_config(notifier_id)
        if not notifier:
            raise HTTPException(status_code=404, detail=f"Notifier '{notifier_id}' 未找到")

        notifier_dict = notifier.model_dump()
        # 隐藏敏感信息
        if 'token' in notifier_dict and notifier_dict['token']:
            notifier_dict['token'] = '***' + notifier_dict['token'][-4:] if len(notifier_dict['token']) > 4 else '***'

        return success_response("获取成功", notifier_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Notifier配置失败: {str(e)}")


@router.post("", dependencies=[Depends(verify_token)])
async def api_create_notifier(config: NotifierCreateModel):
    """创建Notifier配置"""
    try:
        result = await add_notifier_config(config)
        if not result:
            raise HTTPException(status_code=500, detail="保存Notifier配置失败")

        # 返回创建的结果（隐藏敏感信息）
        result = result.model_dump()
        if 'token' in result and result['token']:
            result['token'] = '***' + result['token'][-4:] if len(result['token']) > 4 else '***'

        return success_response("创建成功", result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建Notifier配置失败: {str(e)}")


@router.post("/test", dependencies=[Depends(verify_token)])
async def api_notifier_test(config: NotifierCreateModel):
    """测试Notifier配置（创建测试）"""
    try:
        # 创建临时的NotifierConfig对象用于测试
        test_config = NotifierConfig(**config.model_dump(), id='test')

        # 创建notifier实例
        notifier = NotificationManager._create_notifier_from_config(test_config)
        if not notifier:
            raise HTTPException(status_code=500, detail=f"测试失败，无效配置")

        # 执行测试
        notifier.test()
        return success_response('测试成功', {
            "notifier_name": config.name,
            "notifier_type": config.type
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试Notifier失败: {str(e)}")


@router.post("/{notifier_id}", dependencies=[Depends(verify_token)])
async def api_update_notifier(notifier_id: str, config: NotifierUpdateModel):
    """更新Notifier配置"""
    try:
        # 更新配置
        notifier = await update_notifier_config(notifier_id, config)
        if not notifier:
            raise HTTPException(status_code=500, detail="更新Notifier配置失败")

        result = notifier.model_dump()
        if 'token' in result and result['token']:
            result['token'] = '***' + result['token'][-4:] if len(result['token']) > 4 else '***'

        return success_response("更新成功", result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新Notifier配置失败: {str(e)}")


@router.delete("/{notifier_id}", dependencies=[Depends(verify_token)])
async def api_delete_notifier(notifier_id: str):
    """删除Notifier配置"""
    try:
        # 检查notifier是否存在
        existing_notifier = await get_notifier_config(notifier_id)
        if not existing_notifier:
            raise HTTPException(status_code=404, detail=f"Notifier '{notifier_id}' 未找到")

        # 删除配置
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
        notifier = NotificationManager._create_notifier_from_config(notifier_config)
        if not notifier:
            raise HTTPException(status_code=500, detail="创建Notifier实例失败")

        # 测试连接
        notifier.test()

        return success_response('测试成功', {
            "notifier_id": notifier_id,
            "notifier_name": notifier_config.name,
            "notifier_type": notifier_config.type
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试Notifier失败: {str(e)}")


# --------------- 旧API兼容接口（向后兼容） ----------------
# 注意：这些接口保留用于向后兼容，但建议使用新的notifier API
router_legacy = APIRouter(prefix="/notify", tags=["notify"])


@router_legacy.get("/templates", dependencies=[Depends(verify_token)])
async def api_get_templates_legacy():
    """获取Notifier模板列表（向后兼容）"""
    return await api_get_notifier_templates()


@router_legacy.post("/test", dependencies=[Depends(verify_token)])
async def api_test_legacy(config: dict):
    """测试Notifier（向后兼容）"""
    try:
        notifier = NotificationManager._create_notifier_from_dict(config)
        if not notifier:
            raise HTTPException(status_code=500, detail=f"测试失败，无效配置")

        notifier.test()
        return success_response('测试成功')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")
