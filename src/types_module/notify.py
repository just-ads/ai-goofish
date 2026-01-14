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

NotificationProvider = NtfyConfig | GotifyConfig

# 用于向后兼容，保留旧类型
NotificationProviders = List[NtfyConfig | GotifyConfig]

# 新的：NotificationConfig 中只存储启用的 notifier ID
NotifierIds = List[str]
