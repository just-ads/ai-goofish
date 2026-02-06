"""
类型定义总入口
"""

# 从各个模块导入类型定义
from .config import *
from .notify import *
from .server import *
from .task import *

__all__ = [
    # Config types
    'BrowserConfig', 'AppConfigModel', 'NotificationConfig', 'EvaluatorConfig', 'EvaluationSteps', 'EvaluationStep',

    # Product types
    'Product', 'Seller', 'ProductPriceData', 'Analysis',

    # Task types
    'Task', 'TaskResult', 'TaskResultHistory', 'TaskResultPagination', 'TaskLogEntry', 'TaskRecord',

    # Notify types
    'NtfyConfig', 'GotifyConfig', 'WechatWebhookConfig', 'NotificationProvider', 'NotificationProviders',


    # Server types
    'PaginationOptions', 'GoofishState',

    # Enums
    'TaskResultSortBy'
]
