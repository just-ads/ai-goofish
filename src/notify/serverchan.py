"""Server酱（ServerChan）消息推送。
文档：https://sctapi.ftqq.com/
"""
import re

import httpx

from src.notify.base import BaseNotifier
from src.types import ServerChanConfig


class ServerChanNotifier(BaseNotifier):
    name = "ServerChan"

    def __init__(self, config: ServerChanConfig):
        super().__init__(config)
        self.sendkey = config.get('sendkey', '')
        self.noip = config.get('noip')
        self.channel = config.get('channel')
        self.openid = config.get('openid')

    def _get_url(self) -> str:
        if self.sendkey.startswith('sctp'):
            match = re.search(r'^sctp(\d+)t', self.sendkey)
            if match:
                # group(1) 对应第一个括号内匹配到的数字内容
                num_part = match.group(1)
                return f'https://{num_part}.push.ft07.com/send/{self.sendkey}.send'
            else:
                raise ValueError('Invalid sendkey format')

        return f"https://sctapi.ftqq.com/{self.sendkey}.send"

    def _extra_params(self) -> dict:
        params = {}
        if self.noip:
            params['noip'] = 1
        if self.channel:
            # 前端多选传入列表，API 需要竖线分隔字符串
            if isinstance(self.channel, list):
                params['channel'] = '|'.join(self.channel)
            else:
                params['channel'] = self.channel
        if self.openid:
            params['openid'] = self.openid
        return params

    def test(self):
        resp = httpx.post(
            self._get_url(),
            json={"title": "测试通知", "desp": "你好，准备好接受推荐了吗", **self._extra_params()},
            headers={"Content-Type": "application/json;charset=utf-8"},
            timeout=30,
        )
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Server酱推送失败: {data.get('message', resp.text[:200])}")

    def _do_send(self, data: dict, message: str):
        title = data['title']
        resp = httpx.post(
            self._get_url(),
            json={"title": title, "desp": message, **self._extra_params()},
            headers={"Content-Type": "application/json;charset=utf-8"},
            timeout=30,
        )
        resp_data = resp.json()
        if resp_data.get("code") != 0:
            from src.utils.logger import logger
            logger.error("[ServerChan] 推送失败: {}", resp_data.get("message", resp.text[:200]))
