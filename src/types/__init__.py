"""
类型定义总入口
"""

# 从各个模块导入类型定义
from .config import *
from .task import *
from .server import *
from .notify import *

__all__ = [
    # Config types
    'BrowserConfig', 'AppConfigModel', 'NotificationConfig', 'EvaluatorConfig',

    # Product types
    'Product', 'Seller', 'ProductPriceData', 'Analysis',

    # Task types
    'Task', 'TaskResult', 'TaskResultHistory', 'TaskResultPagination', 'TaskLogEntry',

    # Notify types
    'NtfyConfig', 'GotifyConfig', 'WechatWebhookConfig', 'NotificationProvider', 'NotificationProviders',


    # Server types
    'PaginationOptions', 'GoofishState',

    # Enums
    'TaskResultSortBy'
]
