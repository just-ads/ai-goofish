import os
from datetime import datetime

LOG_LEVEL_INFO = "提示"
LOG_LEVEL_WARNING = "警告"
LOG_LEVEL_ERROR = "错误"
LOG_LEVEL_DEBUG = "DEBUG"


class Logger:
    """日志记录器类"""

    def __init__(self, debug_mode: bool = None):
        """
        初始化日志记录器

        Args:
            debug_mode: 是否启用DEBUG模式，None表示自动检测环境变量
        """
        if debug_mode is None:
            self.debug_mode = os.getenv('DEBUG') == '1'
        else:
            self.debug_mode = debug_mode

    def _log(self, level: str, message: str, *args, **kwargs):
        """内部日志记录方法"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message

        # DEBUG级别日志只在DEBUG模式下输出
        if level == LOG_LEVEL_DEBUG and not self.debug_mode:
            return

        print(f"[{timestamp}] [{level}] {formatted_message}")

    def info(self, message: str, *args, **kwargs):
        """记录提示信息"""
        self._log(LOG_LEVEL_INFO, message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """记录警告信息"""
        self._log(LOG_LEVEL_WARNING, message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """记录错误信息"""
        self._log(LOG_LEVEL_ERROR, message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        """记录调试信息"""
        self._log(LOG_LEVEL_DEBUG, message, *args, **kwargs)


# 创建全局日志记录器实例
logger = Logger()
