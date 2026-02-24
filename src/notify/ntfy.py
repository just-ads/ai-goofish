import httpx

from src.notify.base import BaseNotifier
from src.types import NtfyConfig


def score_tags(score: int):
    if score >= 80:
        return '+1,+1'
    elif score >= 60:
        return '+1'
    elif score >= 30:
        return 'warning'
    else:
        return '-1'


class NtfyNotifier(BaseNotifier):
    name = "Ntfy"

    def __init__(self, config: NtfyConfig):
        super().__init__(config)
        self.topic_url = config.get('url', '').rstrip('/')
        self.message_template = config.get('message_template', None) or (
            '售价：{price}（原价：{origin_price}）\n'
            '发货地：{location} \n'
            'AI分析：{reason} \n'
        )

    def test(self):
        httpx.post(self.topic_url, content='你好，准备好接受推荐了吗', timeout=30)

    def _do_send(self, data: dict, message: str):
        score = data['score']
        tags = score_tags(score) if isinstance(score, (int, float)) else ''
        image = data.get('image', None)
        headers = {
            'Priority': '4',
            'Title': data['title'].encode('utf-8'),
            'Tags': tags,
        }
        if image:
            headers['Attach'] = image
        if data['link']:
            headers['Actions'] = f'view, 查看, {data["link"]}'.encode('utf-8')

        httpx.post(self.topic_url, content=message.encode('utf-8'), headers=headers, timeout=30)
