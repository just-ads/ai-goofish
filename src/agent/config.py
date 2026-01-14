"""
Agent配置管理
"""
import json
from typing import Optional, List, Dict, Any

from pydantic import BaseModel

from src.utils.file_operator import FileOperator
from src.agent.agent import AgentConfig

AGENT_CONFIG_FILE = "agent.config"


class AgentCreateModel(BaseModel):
    """Agent创建模型"""
    name: str
    endpoint: str
    model: str
    api_key: Optional[str] = ""
    proxy: Optional[str] = ""
    headers: Optional[Dict[str, str]] = {"Authorization": "Bearer {key}", "Content-Type": "application/json"}
    body: Optional[Dict[str, Any]] = {"model": "{model}", "messages": "{messages}"}


class AgentUpdateModel(BaseModel):
    """Agent更新请求模型"""
    name: Optional[str] = None
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    proxy: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


async def get_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """
    从agent.config文件获取指定Agent配置

    Args:
        agent_id: Agent ID

    Returns:
        Agent配置对象或None
    """
    agent_file_op = FileOperator(AGENT_CONFIG_FILE)

    data_str = await agent_file_op.read()
    if not data_str:
        return None

    try:
        agents = json.loads(data_str) if data_str else []

        agent = next((item for item in agents if isinstance(item, dict) and item.get('id') == agent_id), None)

        if not agent:
            return None

        try:
            return AgentConfig(**agent)
        except Exception as e:
            raise ValueError(f"Agent配置解析失败: {e}")

    except json.JSONDecodeError as e:
        raise ValueError(f"agent.config文件JSON格式错误: {e}")


async def get_all_agents() -> List[AgentConfig]:
    """
    从agent.config文件获取所有Agent配置

    Returns:
        Agent配置对象列表
    """
    agent_file_op = FileOperator(AGENT_CONFIG_FILE)

    data_str = await agent_file_op.read()
    if not data_str:
        return []

    try:
        agent_dicts = json.loads(data_str) if data_str else []
        agents = []
        for agent_dict in agent_dicts:
            if not isinstance(agent_dict, dict):
                continue

            try:
                agent = AgentConfig(**agent_dict)
                agents.append(agent)
            except Exception as e:
                # 跳过无效配置
                continue

        return agents

    except json.JSONDecodeError as e:
        raise ValueError(f"agent.config文件JSON格式错误: {e}")


async def add_agent_config(agent_config: AgentCreateModel) -> AgentConfig:
    """
    添加Agent配置到agent.config文件

    Args:
        agent_config: Agent字典对象

    Returns:
        添加的Agent配置对象
    """
    agent_file_op = FileOperator(AGENT_CONFIG_FILE)

    data_str = await agent_file_op.read()
    data = json.loads(data_str) if data_str else []

    data.sort(key=lambda item: item['id'])

    agent_id = int(data[-1]['id']) + 1 if data else 0

    agent = agent_config.model_dump(exclude={'id'})

    agent['id'] = str(agent_id)

    data.append(agent)

    await agent_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return AgentConfig(**agent)


async def update_agent_config(agent_id: str, agent_update: AgentUpdateModel) -> AgentConfig:
    """
    更新agent.config文件中的Agent配置

    Args:
        agent_id: 要更新的Agent ID
        agent_update: 更新的Agent配置对象

    Returns:
        更新后的Agent配置对象
    """
    agent_file_op = FileOperator(AGENT_CONFIG_FILE)

    data_str = await agent_file_op.read()
    data = json.loads(data_str) if data_str else []

    # 查找要更新的agent
    agent_index = next((i for i, item in enumerate(data) if item.get('id') == agent_id), -1)

    if agent_index == -1:
        raise ValueError(f"Agent ID {agent_id} 不存在")

    agent = data[agent_index]

    agent.update(agent_update.model_dump(exclude={'id'}))

    await agent_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return AgentConfig(**agent)


async def remove_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """
    从agent.config文件删除Agent配置

    Args:
        agent_id: 要删除的Agent ID

    Returns:
        删除的Agent配置对象或None
    """
    agent_file_op = FileOperator(AGENT_CONFIG_FILE)

    data_str = await agent_file_op.read()
    data = json.loads(data_str) if data_str else []

    agent_index = next((i for i, item in enumerate(data) if item.get('id') == agent_id), -1)

    if agent_index == -1:
        return None

    removed_agent = data.pop(agent_index)

    await agent_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    try:
        return AgentConfig(**removed_agent)
    except Exception:
        return None
