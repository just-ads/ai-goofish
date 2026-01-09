"""
AI服务 - 统一管理Agent客户端
"""
from typing import Optional

from src.agent.client import AgentClient
from src.model.models import AgentConfig
from src.services.agent_service import get_agent_manager
from src.utils.logger import logger


class AIService:
    """AI服务管理器"""

    def __init__(self):
        self._text_client: Optional[AgentClient] = None
        self._image_client: Optional[AgentClient] = None

    def get_text_client(self) -> Optional[AgentClient]:
        """获取文本分析Agent客户端"""
        if self._text_client is not None:
            return self._text_client

        try:
            agent_manager = get_agent_manager()
            agent = agent_manager.get_default_agent()

            if agent is None:
                logger.warning("没有找到默认的文本分析Agent")
                return None

            # 获取完整配置（包含API密钥等敏感信息）
            agent_config = agent_manager.get_agent_config(agent["id"])
            if agent_config is None:
                logger.error(f"无法获取Agent {agent['id']} 的完整配置")
                return None

            # 转换为AgentConfig模型
            config = AgentConfig(
                id=agent_config["id"],
                name=agent_config["name"],
                endpoint=agent_config["endpoint"],
                api_key=agent_config["api_key"],
                model=agent_config["model"],
                proxy=agent_config.get("proxy") or "",
                headers=agent_config.get("headers") or {},
                body=agent_config.get("body") or {}
            )

            self._text_client = AgentClient(config)
            logger.info(f"创建文本分析Agent客户端成功: {agent['name']}")
            return self._text_client

        except Exception as e:
            logger.error(f"创建文本分析Agent客户端失败: {e}")
            return None

    def get_image_client(self) -> Optional[AgentClient]:
        """获取图像分析Agent客户端"""
        # 暂时复用文本客户端，因为图像分析功能尚未完全实现
        return self.get_text_client()

    def refresh_clients(self):
        """刷新客户端缓存"""
        self._text_client = None
        self._image_client = None
        logger.info("Agent客户端缓存已刷新")


# 全局AI服务实例
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """获取全局AI服务实例"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service