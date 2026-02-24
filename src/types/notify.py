"""
Notify 相关类型定义
"""
from typing import TypedDict, Literal, List, NotRequired


class NtfyConfig(TypedDict):
    """Ntfy 配置"""
    type: Literal["ntfy"]
    url: str
    message_template: NotRequired[str]


class GotifyConfig(TypedDict):
    """Gotify 配置"""
    type: Literal["gotify"]
    url: str
    token: str
    message_template: NotRequired[str]


class WechatWebhookConfig(TypedDict):
    """企业微信"消息推送（原群机器人）"Webhook 配置"""
    type: Literal["wechat"]
    key: str
    message_template: NotRequired[str]


class WebhookConfig(TypedDict):
    """通用 Webhook 配置"""
    type: Literal["webhook"]
    url: str
    headers: NotRequired[str]
    message_template: NotRequired[str]


class ServerChanConfig(TypedDict):
    """Server酱（ServerChan）配置"""
    type: Literal["serverchan"]
    sendkey: str
    noip: NotRequired[bool]
    channel: NotRequired[List[str]]
    openid: NotRequired[str]
    message_template: NotRequired[str]

NotificationProvider = NtfyConfig | GotifyConfig | WechatWebhookConfig | ServerChanConfig | WebhookConfig

NotificationProviders = List[NotificationProvider]
