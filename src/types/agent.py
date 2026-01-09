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
    enabled: bool
    is_default: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class AgentCreateRequest(TypedDict):
    """创建Agent请求模型"""
    name: str
    endpoint: str
    api_key: str
    model: str
    proxy: Optional[str]
    headers: Optional[Dict[str, str]]
    body: Optional[Dict[str, Any]]
    enabled: Optional[bool]
    is_default: Optional[bool]


class AgentUpdateRequest(TypedDict, total=False):
    """更新Agent请求模型"""
    name: Optional[str]
    endpoint: Optional[str]
    api_key: Optional[str]
    model: Optional[str]
    proxy: Optional[str]
    headers: Optional[Dict[str, str]]
    body: Optional[Dict[str, Any]]


class AgentResponse(TypedDict):
    """Agent响应模型"""
    id: str
    name: str
    endpoint: str
    model: str
    proxy: Optional[str]


class AgentListResponse(TypedDict):
    """Agent列表响应模型"""
    agents: List[AgentResponse]
    total: int


class AgentsConfigFile(TypedDict):
    """Agent配置文件模型"""
    agents: List[AgentConfigDict]
