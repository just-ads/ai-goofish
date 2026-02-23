from typing import Any

from src.notify.config import get_enabled_notifiers
from src.notify.gotify import GotifyNotifier
from src.notify.ntfy import NtfyNotifier
from src.notify.wechat_service import WechatWebhookNotifier
from src.notify.serverchan import ServerChanNotifier
from src.types import TaskResult, NotificationProvider, NotificationConfig, NotificationProviders


class NotificationManager:
    def __init__(self, providers: NotificationProviders, threshold: float = 60):
        self.notifiers = []
        self.threshold = threshold
        if providers:
            for provider in providers:
                notifier = self.create_notifier(provider)
                if notifier:
                    self.notifiers.append(notifier)

    def notify(self, task_result: TaskResult):
        analysis = task_result.get('分析结果', {})
        if analysis.get('推荐度', 0) < self.threshold:
            return

        for notifier in self.notifiers:
            notifier.send(task_result)

    @staticmethod
    def create_notifier(config: NotificationProvider) -> Any:
        notif_type = config.get('type')
        if notif_type == 'ntfy':
            return NtfyNotifier(config)
        if notif_type == 'gotify':
            return GotifyNotifier(config)
        if notif_type == 'wechat':
            return WechatWebhookNotifier(config)
        if notif_type == 'serverchan':
            return ServerChanNotifier(config)
        return None

    @classmethod
    async def create_from_config(cls, config: NotificationConfig) -> "NotificationManager | None":
        providers = await get_enabled_notifiers()

        if not providers:
            return None

        return cls(
            providers=providers,
            threshold=config.get('threshold', 60)
        )
