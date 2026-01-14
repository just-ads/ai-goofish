"""
config 类型定义模块
"""
from typing import TypedDict, Optional, Literal

from src.types_module.notify import NotifierIds


class BrowserConfig(TypedDict, total=False):
    """浏览器配置"""
    headless: bool
    channel: Literal["chrome", "firefox", "webkit"]


class NotificationConfig(TypedDict, total=False):
    """通知配置"""
    enabled: bool
    providers: NotifierIds  # 只存储启用的notifier ID列表


class EvaluatorConfig(TypedDict, total=False):
    """评估器配置"""
    enabled: bool
    textAgent: Optional[str]
    imagAgent: Optional[str]


class AppConfigModel(TypedDict, total=False):
    """主配置字典"""
    browser: BrowserConfig
    notifications: NotificationConfig
    evaluator: EvaluatorConfig
