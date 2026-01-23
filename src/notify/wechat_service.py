"""企业微信消息推送（原群机器人 Webhook）。

文档：https://developer.work.weixin.qq.com/document/path/99110

该方式不需要 access_token，仅需向 webhook URL POST JSON。
"""

from __future__ import annotations

import httpx

from src.types import TaskResult, WechatWebhookConfig
from src.utils.logger import logger


def _truncate_utf8(text: str, max_bytes: int) -> str:
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text
    return raw[:max_bytes].decode("utf-8", errors="ignore")


class WechatWebhookNotifier:
    def __init__(self, config: WechatWebhookConfig):
        self.webhook_url = config.get("url", "").strip()
        self.msgtype = config.get("msgtype", "markdown")
        self.mentioned_list = config.get("mentioned_list")
        self.mentioned_mobile_list = config.get("mentioned_mobile_list")

    def test(self):
        self._send_text("你好，准备好接受推荐了吗")

    def send(self, task_result: TaskResult):
        try:
            logger.info("推送 [Wechat] 通知，地址为：{}", self.webhook_url)

            product = task_result["商品信息"]
            analysis = task_result.get("分析结果", {}) or {}

            title = str(product.get("商品标题", ""))[:30]
            price = product.get("当前售价", "")
            origin_price = product.get("商品原价", "")
            location = product.get("发货地区", "")
            link = product.get("商品链接", "")
            reason = analysis.get("原因", "")
            score = analysis.get("推荐度", "")

            # 默认用 markdown：更适合展示
            content = "\n".join(
                [
                    f"**{title}**",
                    f"> 售价：{price}（原价：{origin_price}）",
                    f"> 发货地：{location}",
                    f"> 推荐度：{score}",
                    f"> AI分析：{reason}",
                    f"[查看商品]({link})" if link else "",
                ]
            ).strip()

            if self.msgtype == "text":
                content = _truncate_utf8(content, 2048)
                self._send_text(content)
                return

            # markdown / markdown_v2 的 webhook 约束为 4096 bytes
            content = _truncate_utf8(content, 4096)
            self._send_markdown(content)

        except Exception as e:
            logger.error("[Wechat] 通知失败: {}", e)

    def _send_text(self, content: str):
        payload: dict = {
            "msgtype": "text",
            "text": {
                "content": content,
            },
        }

        if self.mentioned_list:
            payload["text"]["mentioned_list"] = self.mentioned_list
        if self.mentioned_mobile_list:
            payload["text"]["mentioned_mobile_list"] = self.mentioned_mobile_list

        self._post(payload)

    def _send_markdown(self, content: str):
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content,
            },
        }
        self._post(payload)

    def _post(self, payload: dict):
        if not self.webhook_url:
            raise ValueError("Wechat webhook url 不能为空")

        resp = httpx.post(self.webhook_url, json=payload, timeout=30)

        # webhook 返回 JSON：{errcode:0, errmsg:'ok'}
        try:
            data = resp.json()
        except Exception:
            logger.error("[Wechat] 响应非 JSON: status={}, body={}", resp.status_code, resp.text[:200])
            return

        errcode = data.get("errcode")
        if errcode not in (0, "0", None):
            logger.error("[Wechat] 推送失败: errcode={}, errmsg={}", errcode, data.get("errmsg"))

