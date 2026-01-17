"""
配置管理
"""

import json
import os
from typing import Dict, Any, List

from src.types import AppConfigModel
from src.utils.logger import logger


class AppConfig:
    """应用配置类"""

    def __init__(self, config_file: str = "app.config"):
        """
        初始化配置

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config: AppConfigModel = self._get_default_config()
        self.load_config()

    @staticmethod
    def _get_default_config() -> AppConfigModel:
        """获取默认配置"""
        return {
            "browser": {
                "headless": True,
                "channel": "chrome"
            },
            "notifications": {
                "enabled": False,
            },
            "evaluator": {
                "enabled": True,
                "textAI": None,
                "imageAI": None,
            }
        }

    def load_config(self) -> bool:
        """从文件加载配置"""
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
                return True

            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            merged_config = self._deep_merge(dict(self.config.copy()), loaded_config)
            self.config = AppConfigModel(**merged_config)

            logger.info(f"配置加载成功: {self.config_file}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON解析失败: {e}")
            return False
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return False

    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

            logger.info(f"配置保存成功: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔（如 "server.port"）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔
            value: 配置值

        Returns:
            是否成功
        """
        try:
            keys = key.split('.')
            config = self.config

            # 遍历到倒数第二个键
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # 设置最后一个键的值
            config[keys[-1]] = value

            # 保存配置
            return self.save_config()

        except Exception as e:
            logger.error(f"设置配置失败: {key} = {value}, 错误: {e}")
            return False

    @property
    def is_notifications_enabled(self) -> bool:
        return self.get('notification.enabled', True)

    @property
    def is_evaluator_enabled(self) -> bool:
        return self.get('evaluator.enabled', True)

    @property
    def evaluator_text_ai(self):
        return self.get('evaluator.textAI', None)

    @property
    def evaluator_image_ai(self):
        return self.get('evaluator.imageAI', None)

    @property
    def browser_headless(self):
        return self.get('browser.headless', True)

    @property
    def browser_channel(self):
        return self.get('browser.channel', 'chrome')

    def update_config(self, updates: AppConfigModel) -> bool:
        """
        批量更新配置

        Args:
            updates: 要更新的配置字典，支持嵌套更新

        Returns:
            是否成功

        Example:
            config.update_config({
                "server": {"port": 8080},
                "browser": {"headless": False}
            })
        """
        try:
            merged_config = self._deep_merge(dict(self.config.copy()), dict(updates.copy()))
            self.config = AppConfigModel(**merged_config)
            return self.save_config()
        except Exception as e:
            logger.error(f"批量更新配置失败: {updates}, 错误: {e}")
            return False

    @staticmethod
    def validate_config(config: AppConfigModel) -> Dict[str, List[str]]:
        """
        验证配置的有效性

        Args:
            config: 要验证的配置字典

        Returns:
            验证错误字典，为空表示验证通过
        """
        errors = {}

        # 验证浏览器配置
        if "browser" in config:
            browser = config["browser"]
            if "headless" in browser and not isinstance(browser["headless"], bool):
                errors.setdefault("browser", []).append("headless 必须是布尔值")
            if "channel" in browser and browser["channel"] not in ["chrome", "firefox", "webkit"]:
                errors.setdefault("browser", []).append("channel 必须是 chrome, firefox, webkit 之一")

        # 验证通知配置
        if "notifications" in config:
            notifications = config["notifications"]
            if "enabled" in notifications and not isinstance(notifications["enabled"], bool):
                errors.setdefault("notifications", []).append("enabled 必须是布尔值")

        # 验证评估器配置
        if "evaluator" in config:
            evaluator = config["evaluator"]
            if "enabled" in evaluator and not isinstance(evaluator["enabled"], bool):
                errors.setdefault("evaluator", []).append("enabled 必须是布尔值")

        return errors

    def validate_current_config(self) -> Dict[str, List[str]]:
        """
        验证当前配置的有效性

        Returns:
            验证错误字典，为空表示验证通过
        """
        return self.validate_config(self.config)

    def set_config(self, config: AppConfigModel) -> bool:
        """
        全量设置配置

        Args:
            config: 完整的配置字典

        Returns:
            是否成功

        Example:
            config.set_config({
                "browser": {"headless": False},
                "agents": [...]
            })
        """
        try:
            validation_errors = self.validate_config(config)
            if validation_errors:
                logger.error(f"配置验证失败: {validation_errors}")
                return False

            # 设置新配置
            self.config = config

            # 保存配置
            return self.save_config()

        except Exception as e:
            logger.error(f"全量设置配置失败: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        return dict(self.config.copy())


# 全局配置实例
_config_instance: AppConfig = AppConfig()


def get_config_instance() -> AppConfig:
    """获取全局配置实例"""
    return _config_instance


def reload_config() -> bool:
    """重新加载配置"""
    return _config_instance.load_config()


def update_global_config(updates: AppConfigModel) -> bool:
    """更新全局配置"""
    return _config_instance.update_config(updates)


def set_global_config(config: AppConfigModel) -> bool:
    """全量设置全局配置"""
    return _config_instance.set_config(config)
