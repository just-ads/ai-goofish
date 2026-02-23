"""Server酱（ServerChan）消息推送。
文档：https://sctapi.ftqq.com/
"""
import httpx

from src.types import ServerChanConfig, TaskResult
from src.utils.logger import logger


class ServerChanNotifier:
    def __init__(self, config: ServerChanConfig):
        self.sendkey = config.get('sendkey', '')
        self.noip = config.get('noip')
        self.channel = config.get('channel')
        self.openid = config.get('openid')

    def _get_url(self) -> str:
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

    def send(self, task_result: TaskResult):
        try:
            logger.info("推送 [ServerChan] 通知")

            product = task_result["商品信息"]
            analysis = task_result.get("分析结果", {}) or {}

            title = str(product.get("商品标题", ""))[:32]
            price = product.get("当前售价", "")
            origin_price = product.get("商品原价", "")
            location = product.get("发货地区", "")
            link = product.get("商品链接", "")
            reason = analysis.get("原因", "")
            score = analysis.get("推荐度", "")

            desp = "\n".join(
                [
                    f"**{title}**",
                    f"> 售价：{price}（原价：{origin_price}）",
                    f"> 发货地：{location}",
                    f"> 推荐度：{score}",
                    f"> AI分析：{reason}",
                    f"[查看商品]({link})" if link else "",
                ]
            ).strip()

            resp = httpx.post(
                self._get_url(),
                json={"title": title, "desp": desp, **self._extra_params()},
                headers={"Content-Type": "application/json;charset=utf-8"},
                timeout=30,
            )

            data = resp.json()
            if data.get("code") != 0:
                logger.error("[ServerChan] 推送失败: {}", data.get("message", resp.text[:200]))

        except Exception as e:
            logger.error("[ServerChan] 通知失败: {}", e)
