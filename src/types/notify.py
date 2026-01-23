"""
Notify 相关类型定义
"""
from typing import TypedDict, Literal, List, NotRequired


class NtfyConfig(TypedDict):
    """Ntfy 配置"""
    type: Literal["ntfy"]
    url: str


class GotifyConfig(TypedDict):
    """Gotify 配置"""
    type: Literal["gotify"]
    url: str
    token: str


class WechatWebhookConfig(TypedDict):
    """企业微信“消息推送（原群机器人）”Webhook 配置"""

    type: Literal["wechat"]
    url: str
    msgtype: NotRequired[Literal["markdown", "text"]]
    mentioned_list: NotRequired[List[str]]
    mentioned_mobile_list: NotRequired[List[str]]


NotificationProvider = NtfyConfig | GotifyConfig | WechatWebhookConfig

NotificationProviders = List[NotificationProvider]

