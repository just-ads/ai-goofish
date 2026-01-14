from typing import Any

from src.notify.gotify import GotifyNotifier
from src.notify.ntfy import NtfyNotifier
from src.types_module import TaskResult, NotificationProviders, NotificationProvider


class NotificationManager:
    def __init__(self, providers: NotificationProviders):
        self.notifiers = []
        if providers:
            for provider in providers:
                notifier = self.create_notifier(provider)
                if notifier:
                    self.notifiers.append(notifier)

    def notify(self, task_result: TaskResult):
        analysis = task_result.get('分析结果', {})
        if analysis.get('推荐度', 0) < 60:
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
        return None
