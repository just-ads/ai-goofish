import os

from src.utils.date import now_str

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

    @staticmethod
    def _format_message(level: str, message: str, *args, **kwargs):
        time = now_str()
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message
        formatted_message = formatted_message.replace('\n', '')
        return f"[{time}] [{level}] {formatted_message}"

    def _log(self, level: str, message: str, *args, **kwargs):
        if level == LOG_LEVEL_DEBUG and not self.debug_mode:
            return

        print(self._format_message(level, message, *args, **kwargs))

    def _log_file(self, file: str, level: str, message: str, *args, **kwargs):
        if level == LOG_LEVEL_DEBUG and not self.debug_mode:
            return
        st = self._format_message(level, message, *args, **kwargs)
        try:
            with open(file, 'a', encoding='utf-8') as f:
                f.write(f"{st}\n")
        except Exception:
            pass

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

    def info_file(self, file: str, message: str, *args, **kwargs):
        self._log_file(file, LOG_LEVEL_INFO, message, *args, **kwargs)

    def warning_file(self, file: str, message: str, *args, **kwargs):
        self._log_file(file, LOG_LEVEL_WARNING, message, *args, **kwargs)

    def error_file(self, file: str, message: str, *args, **kwargs):
        self._log_file(file, LOG_LEVEL_ERROR, message, *args, **kwargs)

    def debug_file(self, file: str, message: str, *args, **kwargs):
        self._log_file(file, LOG_LEVEL_DEBUG, message, *args, **kwargs)


# 创建全局日志记录器实例
logger = Logger()
