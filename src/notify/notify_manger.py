from src.notify.gotify import GotifyNotifier
from src.notify.ntfy import NtfyNotifier
from src.types_module import TaskResult, NotificationProvider


class NotificationManager:
    def __init__(self, providers: NotificationProvider):
        self.notifiers = []
        if providers:
            for provider in providers:
                notif_type = provider.get('type')
                if notif_type == 'ntfy':
                    self.notifiers.append(NtfyNotifier(provider))
                if notif_type == 'gotify':
                    self.notifiers.append(GotifyNotifier(provider))

    def notify(self, task_result: TaskResult):
        analysis = task_result.get('分析结果', {})
        if analysis.get('推荐度', 0) < 60:
            return

        for notifier in self.notifiers:
            notifier.send(task_result)
