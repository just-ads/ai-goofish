"""
Notify 相关类型定义
"""
from typing import TypedDict, Literal, List


class NtfyConfig(TypedDict):
    """Ntfy 配置"""
    type: Literal["ntfy"]
    url: str


class GotifyConfig(TypedDict):
    """Gotify 配置"""
    type: Literal["gotify"]
    url: str
    token: str


NotificationProvider = List[NtfyConfig | GotifyConfig]
