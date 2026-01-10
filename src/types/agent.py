"""
Agent 相关类型定义
"""
from typing import TypedDict, Dict, Any, Optional, List
from datetime import datetime


class AgentConfigDict(TypedDict):
    """Agent 配置模型"""
    id: str
    name: str
    endpoint: str
    api_key: str
    model: str
    proxy: Optional[str]
    headers: Optional[Dict[str, str]]
    body: Optional[Dict[str, Any]]
