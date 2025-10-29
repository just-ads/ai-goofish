import requests


class GotifyNotifier:
    def __init__(self, server_url: str, token: str):
        self.server_url = server_url.rstrip('/')
        self.token = token

    def send(self, task_result: dict):
        try:
            url = f"{self.server_url}/message?token={self.token}"
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
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"[Gotify] 通知失败: {e}")
