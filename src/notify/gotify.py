import httpx

from src.notify.base import BaseNotifier
from src.types import GotifyConfig
from src.utils.logger import logger


class GotifyNotifier(BaseNotifier):
    name = "Gotify"

    def __init__(self, config: GotifyConfig):
        super().__init__(config)
        self.server_url = config.get('url', '').rstrip('/')
        self.token = config.get('token', '')

    def test(self):
        url = f"{self.server_url}/message?token={self.token}"
        httpx.post(url, content='你好，准备好接受推荐了吗', timeout=10)

    def _do_send(self, data: dict, message: str):
        url = f"{self.server_url}/message?token={self.token}"
        logger.info(f"推送 [Gotify] 通知，地址为：{self.server_url}/message?token=**********")
        payload = {
            'title': data['title'],
            'message': message,
            'priority': 5
        }
        httpx.post(url, json=payload, timeout=10)
