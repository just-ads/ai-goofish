import requests


def score_tags(score: int):
    if score >= 80:
        return '+1,+1'
    elif score >= 60:
        return '+1'
    elif score >= 30:
        return 'warning'
    else:
        return '-1'


class NtfyNotifier:
    def __init__(self, topic_url: str):
        self.topic_url = topic_url.rstrip('/')

    def send(self, task_result: dict):
        try:
            product = task_result['商品信息']
            analysis = task_result.get('分析结果', {})
            score = analysis['推荐度']
            title = product['商品标题'][0:10]
            lines = [
                f'售价：{product['当前售价']}（原价：{product['商品原价']}）',
                f'发货地：{product['发货地区']}',
                f'AI分析：{analysis['原因']}'
            ]

            tags = score_tags(score)
            headers = {
                'Priority': '4',
                'Title': title.encode('utf-8'),
                'Attach': product['商品图片列表'][0],
                'Tags': tags,
                'Actions': f'view, 查看, {product['商品链接']}'.encode('utf-8')
            }
            requests.post(self.topic_url, data='\n'.join(lines).encode('utf-8'), headers=headers, timeout=30)
        except Exception as e:
            print(f'[Ntfy] 通知失败: {e}')
