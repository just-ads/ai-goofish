"""
Agent配置管理服务
"""
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.types.agent import (
    AgentConfigDict,
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentResponse,
    AgentListResponse,
    AgentsConfigFile
)
from src.utils.logger import logger


class AgentManager:
    """Agent配置管理器"""

    def __init__(self, agents_file: str = "agents.json"):
        """
        初始化Agent管理器

        Args:
            agents_file: Agent配置文件路径
        """
        self.agents_file = agents_file
        self.agents: List[AgentConfigDict] = []

    def _load_agents(self) -> List[AgentConfigDict]:
        """从文件加载Agent配置"""
        try:
            if not os.path.exists(self.agents_file):
                logger.warning(f"Agent配置文件不存在")
                return self.agents

            with open(self.agents_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self.agents = config_data if config_data else []

            logger.info(f"成功加载 {len(self._agents_cache)} 个Agent配置")
            return self._agents_cache

        except json.JSONDecodeError as e:
            logger.error(f"Agent配置文件JSON解析失败: {e}")
            self._agents_cache = []
            return self._agents_cache
        except Exception as e:
            logger.error(f"加载Agent配置文件失败: {e}")
            self._agents_cache = []
            return self._agents_cache

    def _save_agents(self) -> bool:
        """保存Agent配置到文件"""
        try:
            config_data: AgentsConfigFile = {
                "agents": self._agents_cache or []
            }

            with open(self.agents_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Agent配置保存成功: {self.agents_file}")
            return True

        except Exception as e:
            logger.error(f"保存Agent配置文件失败: {e}")
            return False

    def _clear_cache(self):
        """清除缓存"""
        self._agents_cache = []

    def _to_response(self, agent: AgentConfigDict) -> AgentResponse:
        """转换为响应模型"""
        return {
            "id": agent["id"],
            "name": agent["name"],
            "endpoint": agent["endpoint"],
            "model": agent["model"],
            "proxy": agent.get("proxy"),
            "enabled": agent.get("enabled", True),
            "is_default": agent.get("is_default", False),
            "created_at": agent.get("created_at", datetime.now().isoformat()) or datetime.now().isoformat(),
            "updated_at": agent.get("updated_at", datetime.now().isoformat()) or datetime.now().isoformat()
        }

    def list_agents(self) -> AgentListResponse:
        """
        获取所有Agent列表

        Returns:
            Agent列表响应
        """
        agents = self._load_agents()
        agent_responses = [self._to_response(agent) for agent in agents]

        return {
            "agents": agent_responses,
            "total": len(agent_responses)
        }

    def get_agent(self, agent_id: str) -> Optional[AgentResponse]:
        """
        获取指定Agent配置

        Args:
            agent_id: Agent ID

        Returns:
            Agent响应或None
        """
        agents = self._load_agents()

        for agent in agents:
            if agent["id"] == agent_id:
                return self._to_response(agent)

        return None

    def create_agent(self, agent_data: AgentCreateRequest) -> Optional[AgentResponse]:
        """
        创建新Agent

        Args:
            agent_data: Agent创建请求数据

        Returns:
            创建的Agent响应或None
        """
        agents = self._load_agents()

        # 检查ID是否已存在
        agent_id = agent_data.get("id") or f"agent-{int(datetime.now().timestamp())}"
        for agent in agents:
            if agent["id"] == agent_id:
                logger.error(f"Agent ID已存在: {agent_id}")
                return None

        # 如果设置为默认，先取消其他默认设置
        if agent_data.get("is_default", False):
            for agent in agents:
                agent["is_default"] = False

        # 创建新Agent
        now = datetime.now().isoformat()

        new_agent_data: Dict[str, Any] = {
            "id": agent_id,
            "name": agent_data["name"],
            "endpoint": agent_data["endpoint"],
            "api_key": agent_data["api_key"],
            "model": agent_data["model"],
            "proxy": agent_data.get("proxy"),
            "created_at": now,
            "updated_at": now
        }

        # 可选字段
        if agent_data.get("headers") is not None:
            new_agent_data["headers"] = agent_data["headers"]
        if agent_data.get("body") is not None:
            new_agent_data["body"] = agent_data["body"]

        new_agent_data["enabled"] = agent_data.get("enabled") if agent_data.get("enabled") is not None else True
        new_agent_data["is_default"] = agent_data.get("is_default") if agent_data.get("is_default") is not None else False

        new_agent: AgentConfigDict = AgentConfigDict(**new_agent_data)

        agents.append(new_agent)

        if self._save_agents():
            self._clear_cache()
            logger.info(f"成功创建Agent: {agent_id}")
            return self._to_response(new_agent)

        return None

    def update_agent(self, agent_id: str, agent_data: AgentUpdateRequest) -> Optional[AgentResponse]:
        """
        更新Agent配置

        Args:
            agent_id: Agent ID
            agent_data: Agent更新请求数据

        Returns:
            更新后的Agent响应或None
        """
        agents = self._load_agents()

        for i, agent in enumerate(agents):
            if agent["id"] == agent_id:
                # 如果设置为默认，先取消其他默认设置
                if agent_data.get("is_default", False):
                    for other_agent in agents:
                        other_agent["is_default"] = False

                # 更新Agent
                updated_agent = agents[i].copy()

                # 手动更新每个字段以避免类型问题
                if "name" in agent_data and agent_data["name"] is not None:
                    updated_agent["name"] = agent_data["name"]
                if "endpoint" in agent_data and agent_data["endpoint"] is not None:
                    updated_agent["endpoint"] = agent_data["endpoint"]
                if "api_key" in agent_data and agent_data["api_key"] is not None:
                    updated_agent["api_key"] = agent_data["api_key"]
                if "model" in agent_data and agent_data["model"] is not None:
                    updated_agent["model"] = agent_data["model"]
                if "proxy" in agent_data:
                    updated_agent["proxy"] = agent_data["proxy"]
                if "headers" in agent_data:
                    updated_agent["headers"] = agent_data["headers"]
                if "body" in agent_data:
                    updated_agent["body"] = agent_data["body"]
                if "enabled" in agent_data and agent_data["enabled"] is not None:
                    updated_agent["enabled"] = agent_data["enabled"]
                if "is_default" in agent_data and agent_data["is_default"] is not None:
                    updated_agent["is_default"] = agent_data["is_default"]

                updated_agent["updated_at"] = datetime.now().isoformat()

                agents[i] = updated_agent

                if self._save_agents():
                    self._clear_cache()
                    logger.info(f"成功更新Agent: {agent_id}")
                    return self._to_response(updated_agent)

                return None

        logger.error(f"Agent不存在: {agent_id}")
        return None

    def delete_agent(self, agent_id: str) -> bool:
        """
        删除Agent

        Args:
            agent_id: Agent ID

        Returns:
            是否成功删除
        """
        agents = self._load_agents()
        original_count = len(agents)

        # 检查是否存在
        agent_exists = any(agent["id"] == agent_id for agent in agents)
        if not agent_exists:
            logger.error(f"Agent不存在: {agent_id}")
            return False

        # 删除Agent
        agents = [agent for agent in agents if agent["id"] != agent_id]

        if len(agents) == original_count - 1 and self._save_agents():
            self._clear_cache()
            logger.info(f"成功删除Agent: {agent_id}")
            return True

        logger.error(f"删除Agent失败: {agent_id}")
        return False

    def get_default_agent(self) -> Optional[AgentResponse]:
        """
        获取默认Agent

        Returns:
            默认Agent响应或None
        """
        agents = self._load_agents()

        for agent in agents:
            if agent.get("is_default", False):
                return self._to_response(agent)

        # 如果没有默认Agent，返回第一个启用的Agent
        for agent in agents:
            if agent.get("enabled", True):
                return self._to_response(agent)

        return None

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfigDict]:
        """
        获取Agent完整配置（包含敏感信息）

        Args:
            agent_id: Agent ID

        Returns:
            Agent完整配置或None
        """
        agents = self._load_agents()

        for agent in agents:
            if agent["id"] == agent_id:
                return agent.copy()

        return None

    def set_default_agent(self, agent_id: str) -> bool:
        """
        设置默认Agent

        Args:
            agent_id: Agent ID

        Returns:
            是否成功设置
        """
        agents = self._load_agents()

        # 检查Agent是否存在
        agent_exists = any(agent["id"] == agent_id for agent in agents)
        if not agent_exists:
            logger.error(f"Agent不存在: {agent_id}")
            return False

        # 取消所有默认设置，设置新的默认
        for agent in agents:
            agent["is_default"] = (agent["id"] == agent_id)
            if agent["id"] == agent_id:
                agent["updated_at"] = datetime.now().isoformat()

        if self._save_agents():
            self._clear_cache()
            logger.info(f"成功设置默认Agent: {agent_id}")
            return True

        return False

    def validate_agent_config(self, agent_data: Dict[str, Any]) -> List[str]:
        """
        验证Agent配置

        Args:
            agent_data: Agent配置数据

        Returns:
            验证错误列表
        """
        errors = []

        # 必填字段验证
        required_fields = ["name", "endpoint", "api_key", "model"]
        for field in required_fields:
            if field not in agent_data or not agent_data[field]:
                errors.append(f"缺少必填字段: {field}")

        # URL格式验证
        if "endpoint" in agent_data:
            endpoint = agent_data["endpoint"]
            if not (endpoint.startswith("http://") or endpoint.startswith("https://")):
                errors.append("endpoint必须以http://或https://开头")

        # 代理URL格式验证
        if "proxy" in agent_data and agent_data["proxy"]:
            proxy = agent_data["proxy"]
            if not (proxy.startswith("http://") or proxy.startswith("https://") or
                   proxy.startswith("socks5://")):
                errors.append("proxy必须以http://、https://或socks5://开头")

        return errors


# 全局Agent管理器实例
_agent_manager: Optional[AgentManager] = None


def get_agent_manager() -> AgentManager:
    """获取全局Agent管理器实例"""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager