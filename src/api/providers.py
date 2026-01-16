"""
Model provider routes.

Manage provider configurations (CRUD), connectivity tests, and chat.
"""
from typing import List
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.model_provider.models import AiConfig, ChatMessage, ProviderPresetTemplate
from src.model_provider.client import ProviderClient
from src.model_provider.config import (
    get_provider_config, get_all_providers,
    add_provider_config, update_provider_config,
    remove_provider_config, ProviderCreateModel, ProviderUpdateModel
)
from src.api.auth import verify_token
from src.api.utils import success_response

# 创建路由器
router = APIRouter(prefix="/providers", tags=["providers"])



# --------------- Provider templates ----------------
@router.get("/templates", dependencies=[Depends(verify_token)])
async def api_get_provider_templates():
    """获取 Provider 预设模板列表"""
    try:
        templates = ProviderPresetTemplate.get_preset_templates()
        template_list = [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "endpoint": template.endpoint,
                "api_key": template.api_key,
                "model": template.model,
                "headers": template.headers,
                "body": template.body
            }
            for template in templates
        ]
        return success_response('获取成功', template_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")


# --------------- Provider config CRUD ----------------
@router.get("", dependencies=[Depends(verify_token)])
async def api_get_providers():
    """获取所有 Provider 配置"""
    try:
        providers = await get_all_providers()
        # 转换为字典列表
        provider_list = []
        for provider in providers:
            if provider:
                provider_dict = provider.model_dump()
                # 隐藏敏感信息
                if 'api_key' in provider_dict and provider_dict['api_key']:
                    provider_dict['api_key'] = '***' + provider_dict['api_key'][-4:] if len(provider_dict['api_key']) > 4 else '***'
                provider_list.append(provider_dict)

        return success_response("获取成功", provider_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Provider配置失败: {str(e)}")


@router.post("", dependencies=[Depends(verify_token)])
async def api_create_provider(config: ProviderCreateModel):
    """创建 Provider 配置"""
    try:
        result = await add_provider_config(config)
        if not result:
            raise HTTPException(status_code=500, detail="保存Provider配置失败")

        # 返回创建的结果（隐藏敏感信息）
        result = result.model_dump()
        if 'api_key' in result and result['api_key']:
            result['api_key'] = '***' + result['api_key'][-4:] if len(result['api_key']) > 4 else '***'

        return success_response("创建成功", result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建Provider配置失败: {str(e)}")


@router.get("/{provider_id}", dependencies=[Depends(verify_token)])
async def api_get_provider(provider_id: str):
    """获取单个 Provider 配置"""
    try:
        provider = await get_provider_config(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' 未找到")

        provider_dict = provider.model_dump()
        # 隐藏敏感信息
        if 'api_key' in provider_dict and provider_dict['api_key']:
            provider_dict['api_key'] = '***' + provider_dict['api_key'][-4:] if len(provider_dict['api_key']) > 4 else '***'

        return success_response("获取成功", provider_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Provider配置失败: {str(e)}")


@router.post("/test", dependencies=[Depends(verify_token)])
async def api_provider_test(config: ProviderCreateModel):
    try:
        client = ProviderClient(AiConfig(**config.model_dump(), id='test'))
        messages = await client.ask(messages=[{"role": "user", "content": "Hello."}])
        return success_response('测试成功', {
            "provider_name": config.name,
            "response": f'{messages.content}'
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试Provider失败: {str(e)}")


@router.post("/{provider_id}", dependencies=[Depends(verify_token)])
async def api_update_provider(provider_id: str, config: ProviderUpdateModel):
    """更新 Provider 配置"""
    try:

        # 更新配置
        provider = await update_provider_config(provider_id, config)
        if not provider:
            raise HTTPException(status_code=500, detail="更新Provider配置失败")

        result = provider.model_dump()
        if 'api_key' in result and result['api_key']:
            result['api_key'] = '***' + result['api_key'][-4:] if len(result['api_key']) > 4 else '***'

        return success_response("更新成功", result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新Provider配置失败: {str(e)}")


@router.delete("/{provider_id}", dependencies=[Depends(verify_token)])
async def api_delete_provider(provider_id: str):
    """删除 Provider 配置"""
    try:
        # 检查 provider 是否存在
        existing_provider = await get_provider_config(provider_id)
        if not existing_provider:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' 未找到")

        # 删除配置
        result = await remove_provider_config(provider_id)
        if not result:
            raise HTTPException(status_code=500, detail="删除Provider配置失败")

        return success_response("删除成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除Provider配置失败: {str(e)}")


# --------------- Provider operations ----------------
@router.post("/{provider_id}/test", dependencies=[Depends(verify_token)])
async def api_test_provider(provider_id: str):
    """测试 Provider 连接"""
    try:
        # 获取 provider 配置
        provider_config = await get_provider_config(provider_id)
        if not provider_config:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' 未找到")

        # 测试连接
        client = ProviderClient(provider_config)
        messages = await client.ask(messages=[{"role": "user", "content": "Hello."}])

        return success_response('测试成功', {
            "provider_id": provider_id,
            "provider_name": provider_config.name,
            "response": f'{messages.content}'
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试Provider失败: {str(e)}")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage]
    parameters: Optional[dict] = None


@router.post("/{provider_id}/chat", dependencies=[Depends(verify_token)])
async def api_chat_with_provider(provider_id: str, request: ChatRequest):
    """与 Provider 进行对话"""
    try:
        # 获取 provider 配置
        provider_config = await get_provider_config(provider_id)
        if not provider_config:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' 未找到")

        # 进行对话
        client = ProviderClient(provider_config)
        response = client.ask(
            messages=request.messages,
            parameters=request.parameters
        )

        return success_response('对话成功', {
            "provider_id": provider_id,
            "provider_name": provider_config.name,
            "response": response
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"与Provider对话失败: {str(e)}")
