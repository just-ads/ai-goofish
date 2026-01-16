import httpx

from src.types import GotifyConfig, TaskResult
from src.utils.logger import logger


class GotifyNotifier:
    def __init__(self, config: GotifyConfig):
        self.server_url = config.get('url', '').rstrip('/')
        self.token = config.get('token', '')

    def test(self):
        url = f"{self.server_url}/message?token={self.token}"
        httpx.post(url, content='你好，准备好接受推荐了吗', timeout=10)

    def send(self, task_result: TaskResult):
        try:
            url = f"{self.server_url}/message?token={self.token}"
            logger.info("推送 [Gotify] 通知，地址为：{}", url)
            product = task_result['商品信息']
            analysis = task_result.get('分析结果', {})
            title = product['商品标题'][0:10]
            lines = [
                f'售价：{product['当前售价']}（原价：{product['商品原价']}）',
                f'发货地：{product['发货地区']}',
                f'AI分析：{analysis['原因']}'
            ]
            payload = {
                'title': title,
                'message': '\n'.join(lines),
                'priority': 5
            }
            httpx.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error("[Gotify] 通知失败: {}", e)
