"""
AI routes.

Manage AI configurations (CRUD), connectivity tests, and chat.
"""
from typing import List
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.ai.models import AIConfig, AIMessage, AIPresetTemplate
from src.ai.client import AIClient
from src.ai.config import (
    get_ai_config, get_all_ai_config,
    add_ai_config, update_ai_config,
    remove_ai_config, AICreateModel, AIUpdateModel
)
from src.api.auth import verify_token
from src.api.utils import success_response
from src.utils.secrecy import secrecy_value, is_secrecy_value

router = APIRouter(prefix="/ai", tags=["ai"])


# --------------- AI templates ----------------
@router.get("/templates", dependencies=[Depends(verify_token)])
async def api_get_ai_templates():
    """获取 AI 预设模板列表"""
    try:
        templates = AIPresetTemplate.get_preset_templates()
        template_list = [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "api_key_domin": template.api_key_domin,
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


# --------------- AI config CRUD ----------------
@router.get("", dependencies=[Depends(verify_token)])
async def api_get_ais():
    """获取所有 AI 配置"""
    try:
        configs = await get_all_ai_config()
        ai_list = []
        for config in configs:
            if config:
                provider_dict = config.model_dump()
                if 'api_key' in provider_dict and provider_dict['api_key']:
                    provider_dict['api_key'] = secrecy_value(provider_dict['api_key'])
                ai_list.append(provider_dict)

        return success_response("获取成功", ai_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI配置失败: {str(e)}")


@router.post("", dependencies=[Depends(verify_token)])
async def api_create_ai(config: AICreateModel):
    """创建 AI 配置"""
    try:
        config = await add_ai_config(config)
        if not config:
            raise HTTPException(status_code=500, detail="保存AI配置失败")

        config = config.model_dump()
        if 'api_key' in config and config['api_key']:
            config['api_key'] = secrecy_value(config['api_key'])

        return success_response("创建成功", config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建AI配置失败: {str(e)}")


@router.post("/test", dependencies=[Depends(verify_token)])
async def api_ai_test(config: AICreateModel):
    try:
        client = AIClient(AIConfig(**config.model_dump(), id='test'))

        if config.multimodal:
            response = await client.ask(
                messages=[{
                    "role": 'user',
                    'content': [
                        {'type': 'text', 'text': '描述图片'},
                        {'type': 'image_url', 'image_url': 'https://inews.gtimg.com/om_bt/OsbU7Hilx3AaiHWB45v3QuxwkOeKDNrAaU1AxGLcH2xcIAA/641'},
                    ]
                }],
                max_retries=2
            )
        else:
            response = await client.ask(messages=[{"role": "user", "content": "Hello."}], max_retries=2)

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        return success_response('测试成功', {
            "provider_name": config.name,
            "response": f'{response.content}'
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试AI失败: {str(e)}")


@router.get("/{id}", dependencies=[Depends(verify_token)])
async def api_get_ai(id: str):
    """获取单个 AI 配置"""
    try:
        config = await get_ai_config(id)
        if not config:
            raise HTTPException(status_code=404, detail=f"AI '{id}' 未找到")

        config = config.model_dump()
        if 'api_key' in config and config['api_key']:
            config['api_key'] = secrecy_value(config['api_key'])

        return success_response("获取成功", config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI配置失败: {str(e)}")


@router.post("/{id}", dependencies=[Depends(verify_token)])
async def api_update_provider(id: str, config: AIUpdateModel):
    """更新 AI 配置"""
    try:
        config = await update_ai_config(
            id,
            config,
            exclude={"api_key"} if is_secrecy_value(config.api_key) else None
        )
        if not config:
            raise HTTPException(status_code=500, detail="更新AI配置失败")

        config = config.model_dump()
        if 'api_key' in config and config['api_key']:
            config['api_key'] = secrecy_value(config['api_key'])

        return success_response("更新成功", config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新AI配置失败: {str(e)}")


@router.delete("/{id}", dependencies=[Depends(verify_token)])
async def api_delete_provider(id: str):
    """删除 AI 配置"""
    try:
        config = await get_ai_config(id)
        if not config:
            raise HTTPException(status_code=404, detail=f"AI '{id}' 未找到")

        config = await remove_ai_config(id)
        if not config:
            raise HTTPException(status_code=500, detail="删除AI配置失败")

        return success_response("删除成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除AI配置失败: {str(e)}")


# --------------- AI operations ----------------
@router.post("/{id}/test", dependencies=[Depends(verify_token)])
async def api_test_provider(id: str):
    """测试 AI 连接"""
    try:
        config = await get_ai_config(id)
        if not config:
            raise HTTPException(status_code=404, detail=f"AI '{id}' 未找到")

        client = AIClient(config)

        if config.multimodal:
            response = await client.ask(
                messages=[{
                    "role": 'user',
                    'content': [
                        {'type': 'text', 'text': '描述图片'},
                        {'type': 'image_url', 'image_url': 'https://inews.gtimg.com/om_bt/OsbU7Hilx3AaiHWB45v3QuxwkOeKDNrAaU1AxGLcH2xcIAA/641'},
                    ]
                }],
                max_retries=2
            )
        else:
            response = await client.ask(messages=[{"role": "user", "content": "Hello."}], max_retries=2)

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        return success_response('测试成功', {
            "provider_name": config.name,
            "response": f'{response.content}'
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试AI失败: {str(e)}")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[AIMessage]
    parameters: Optional[dict] = None


@router.post("/{id}/chat", dependencies=[Depends(verify_token)])
async def api_chat_with_provider(id: str, request: ChatRequest):
    """与 AI 进行对话"""
    try:
        config = await get_ai_config(id)
        if not config:
            raise HTTPException(status_code=404, detail=f"AI '{id}' 未找到")

        client = AIClient(config)
        response = await client.ask(
            messages=request.messages,
            parameters=request.parameters
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        return success_response('对话成功', {
            "provider_id": id,
            "provider_name": config.name,
            "response": response
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"与AI对话失败: {str(e)}")
