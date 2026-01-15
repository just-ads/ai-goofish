"""
Agent相关路由模块
处理Agent配置的增删改查、测试、对话等功能
"""
from typing import List
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.agent.agent import AgentConfig, AgentMessage, AgentPresetTemplate
from src.agent.client import AgentClient
from src.agent.config import (
    get_agent_config, get_all_agents,
    add_agent_config, update_agent_config,
    remove_agent_config, AgentCreateModel, AgentUpdateModel
)
from src.api.auth import verify_token
from src.api.utils import success_response

# 创建路由器
router = APIRouter(prefix="/agents", tags=["agents"])


# --------------- Agent模板接口 ----------------
@router.get("/templates", dependencies=[Depends(verify_token)])
async def api_get_agent_templates():
    """获取Agent预设模板列表"""
    try:
        templates = AgentPresetTemplate.get_preset_templates()
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


# --------------- Agent配置管理接口 ----------------
@router.get("", dependencies=[Depends(verify_token)])
async def api_get_agents():
    """获取所有Agent配置"""
    try:
        agents = await get_all_agents()
        # 转换为字典列表
        agent_list = []
        for agent in agents:
            if agent:
                agent_dict = agent.model_dump()
                # 隐藏敏感信息
                if 'api_key' in agent_dict and agent_dict['api_key']:
                    agent_dict['api_key'] = '***' + agent_dict['api_key'][-4:] if len(agent_dict['api_key']) > 4 else '***'
                agent_list.append(agent_dict)

        return success_response("获取成功", agent_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Agent配置失败: {str(e)}")


@router.post("", dependencies=[Depends(verify_token)])
async def api_create_agent(config: AgentCreateModel):
    """创建Agent配置"""
    try:
        result = await add_agent_config(config)
        if not result:
            raise HTTPException(status_code=500, detail="保存Agent配置失败")

        # 返回创建的结果（隐藏敏感信息）
        result = result.model_dump()
        if 'api_key' in result and result['api_key']:
            result['api_key'] = '***' + result['api_key'][-4:] if len(result['api_key']) > 4 else '***'

        return success_response("创建成功", result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建Agent配置失败: {str(e)}")


@router.get("/{agent_id}", dependencies=[Depends(verify_token)])
async def api_get_agent(agent_id: str):
    """获取单个Agent配置"""
    try:
        agent = await get_agent_config(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' 未找到")

        agent_dict = agent.model_dump()
        # 隐藏敏感信息
        if 'api_key' in agent_dict and agent_dict['api_key']:
            agent_dict['api_key'] = '***' + agent_dict['api_key'][-4:] if len(agent_dict['api_key']) > 4 else '***'

        return success_response("获取成功", agent_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Agent配置失败: {str(e)}")


@router.post("/test", dependencies=[Depends(verify_token)])
async def api_agent_test(config: AgentCreateModel):
    try:
        client = AgentClient(AgentConfig(**config.model_dump(), id='test'))
        messages = await client.ask(messages=[{"role": "user", "content": "Hello."}])
        return success_response('测试成功', {
            "agent_name": config.name,
            "response": f'{messages.content}'
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试Agent失败: {str(e)}")


@router.post("/{agent_id}", dependencies=[Depends(verify_token)])
async def api_update_agent(agent_id: str, config: AgentUpdateModel):
    """更新Agent配置"""
    try:

        # 更新配置
        agent = await update_agent_config(agent_id, config)
        if not agent:
            raise HTTPException(status_code=500, detail="更新Agent配置失败")

        result = agent.model_dump()
        if 'api_key' in result and result['api_key']:
            result['api_key'] = '***' + result['api_key'][-4:] if len(result['api_key']) > 4 else '***'

        return success_response("更新成功", result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新Agent配置失败: {str(e)}")


@router.delete("/{agent_id}", dependencies=[Depends(verify_token)])
async def api_delete_agent(agent_id: str):
    """删除Agent配置"""
    try:
        # 检查agent是否存在
        existing_agent = await get_agent_config(agent_id)
        if not existing_agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' 未找到")

        # 删除配置
        result = await remove_agent_config(agent_id)
        if not result:
            raise HTTPException(status_code=500, detail="删除Agent配置失败")

        return success_response("删除成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除Agent配置失败: {str(e)}")


# --------------- Agent操作接口 ----------------
@router.post("/{agent_id}/test", dependencies=[Depends(verify_token)])
async def api_test_agent(agent_id: str):
    """测试Agent连接"""
    try:
        # 获取agent配置
        agent_config = await get_agent_config(agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' 未找到")

        # 测试连接
        client = AgentClient(agent_config)
        messages = await client.ask(messages=[{"role": "user", "content": "Hello."}])

        return success_response('测试成功', {
            "agent_id": agent_id,
            "agent_name": agent_config.name,
            "response": f'{messages.content}'
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试Agent失败: {str(e)}")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[AgentMessage]
    parameters: Optional[dict] = None


@router.post("/{agent_id}/chat", dependencies=[Depends(verify_token)])
async def api_chat_with_agent(agent_id: str, request: ChatRequest):
    """与Agent进行对话"""
    try:
        # 获取agent配置
        agent_config = await get_agent_config(agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' 未找到")

        # 进行对话
        client = AgentClient(agent_config)
        response = client.ask(
            messages=request.messages,
            parameters=request.parameters
        )

        return success_response('对话成功', {
            "agent_id": agent_id,
            "agent_name": agent_config.name,
            "response": response
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"与Agent对话失败: {str(e)}")
