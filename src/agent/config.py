"""
Agent配置管理
"""
import json
from typing import Optional, List

from src.utils.file_operator import FileOperator
from src.agent.agent import AgentConfig

AGENT_CONFIG_FILE = "agent.config"


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
        # 尝试解析JSON数据
        agents = json.loads(data_str) if data_str else []

        # 检查数据结构，可能是数组也可能是字典
        agent = next((item for item in agents if isinstance(item, dict) and item.get('id') == agent_id), None)

        if not agent:
            return None

        # 转换为AgentConfig模型
        try:
            return AgentConfig(
                id=agent.get('id', ''),
                name=agent.get('name', ''),
                endpoint=agent.get('endpoint', ''),
                api_key=agent.get('api_key', ''),
                model=agent.get('model', ''),
                proxy=agent.get('proxy', '') if agent.get('proxy') is not None else '',
                headers=agent.get('headers', {}),
                body=agent.get('body', {})
            )
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
        agents = json.loads(data_str) if data_str else []

        for agent in agents:
            if not isinstance(agent, dict):
                continue

            try:
                # 过滤掉禁用的agent
                if not agent.get('enabled', True):
                    continue

                agent = AgentConfig(
                    id=agent.get('id', ''),
                    name=agent.get('name', ''),
                    endpoint=agent.get('endpoint', ''),
                    api_key=agent.get('api_key', ''),
                    model=agent.get('model', ''),
                    proxy=agent.get('proxy', '') if agent.get('proxy') is not None else '',
                    headers=agent.get('headers', {}),
                    body=agent.get('body', {})
                )
                agents.append(agent)
            except Exception as e:
                # 跳过无效配置
                continue

        return agents

    except json.JSONDecodeError as e:
        raise ValueError(f"agent.config文件JSON格式错误: {e}")


async def add_agent_config(agent_config: AgentConfig) -> AgentConfig:
    """
    添加Agent配置到agent.config文件

    Args:
        agent_config: Agent配置对象

    Returns:
        添加的Agent配置对象
    """
    agent_file_op = FileOperator(AGENT_CONFIG_FILE)

    data_str = await agent_file_op.read()
    data = json.loads(data_str) if data_str else []

    # 转换AgentConfig为字典
    agent_dict = {
        'id': agent_config.id,
        'name': agent_config.name,
        'endpoint': agent_config.endpoint,
        'api_key': agent_config.api_key,
        'model': agent_config.model,
        'proxy': agent_config.proxy,
        'headers': agent_config.headers,
        'body': agent_config.body
    }

    data.append(agent_dict)

    await agent_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return agent_config


async def update_agent_config(agent_id: str, agent_update: AgentConfig) -> AgentConfig:
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

    # 更新agent配置
    updated_agent = {
        'id': agent_id,
        'name': agent_update.name,
        'endpoint': agent_update.endpoint,
        'api_key': agent_update.api_key,
        'model': agent_update.model,
        'proxy': agent_update.proxy,
        'headers': agent_update.headers,
        'body': agent_update.body
    }

    data[agent_index] = updated_agent

    await agent_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return agent_update


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

    # 查找要删除的agent
    agent_index = next((i for i, item in enumerate(data) if item.get('id') == agent_id), -1)

    if agent_index == -1:
        return None

    removed_agent = data.pop(agent_index)

    await agent_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    # 转换回AgentConfig对象
    try:
        return AgentConfig(
            id=removed_agent.get('id', ''),
            name=removed_agent.get('name', ''),
            endpoint=removed_agent.get('endpoint', ''),
            api_key=removed_agent.get('api_key', ''),
            model=removed_agent.get('model', ''),
            proxy=removed_agent.get('proxy', ''),
            headers=removed_agent.get('headers', {}),
            body=removed_agent.get('body', {})
        )
    except Exception:
        # 如果转换失败，返回原始数据
        return None
