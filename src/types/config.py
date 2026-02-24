"""
config 类型定义模块
"""
from typing import TypedDict, Optional, Literal


class BrowserConfig(TypedDict, total=False):
    """浏览器配置"""
    headless: bool
    channel: Literal["chromium", "chrome", "firefox", "webkit"]


class NotificationConfig(TypedDict, total=False):
    """通知配置"""
    enabled: bool
    threshold: float


class EvaluationStep(TypedDict, total=False):
    disabled: bool
    threshold: float
    prompt: str


class EvaluationSteps(TypedDict, total=False):
    step1: EvaluationStep
    step2: EvaluationStep
    step3: EvaluationStep
    step4: EvaluationStep


class EvaluatorConfig(TypedDict, total=False):
    """评估器配置"""
    enabled: bool
    textAI: Optional[str]
    imageAI: Optional[str]
    steps: EvaluationSteps


class AppConfigModel(TypedDict, total=False):
    """主配置字典"""
    browser: BrowserConfig
    notifications: NotificationConfig
    evaluator: EvaluatorConfig
