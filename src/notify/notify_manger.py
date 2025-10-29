from src.config import NTFY_TOPIC_URL, GOTIFY_URL, GOTIFY_TOKEN
from src.notify.gotify import GotifyNotifier
from src.notify.ntfy import NtfyNotifier


class NotificationManager:
    def __init__(self):
        self.notifiers = []

        if NTFY_TOPIC_URL:
            self.notifiers.append(NtfyNotifier(NTFY_TOPIC_URL))

        if GOTIFY_URL and GOTIFY_TOKEN:
            self.notifiers.append(GotifyNotifier(GOTIFY_URL, GOTIFY_TOKEN))

    def notify(self, task_result: dict):
        analysis = task_result.get('分析结果', None)
        if analysis:
            if analysis.get('推荐度', 0) < 60:
                return

        for notifier in self.notifiers:
            notifier.send(task_result)
