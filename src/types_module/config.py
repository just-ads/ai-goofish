"""
config 类型定义模块
"""
from typing import TypedDict, Optional, Literal, List


class BrowserConfig(TypedDict, total=False):
    """浏览器配置"""
    headless: bool
    channel: Literal["chrome", "firefox", "webkit"]


class NotificationConfig(TypedDict, total=False):
    """通知配置"""
    enabled: bool
    providers: List[str]


class EvaluatorConfig(TypedDict, total=False):
    """评估器配置"""
    enabled: bool
    textProvider: Optional[str]
    imageProvider: Optional[str]



class AppConfigModel(TypedDict, total=False):
    """主配置字典"""
    browser: BrowserConfig
    notifications: NotificationConfig
    evaluator: EvaluatorConfig
