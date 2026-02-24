"""企业微信消息推送（原群机器人 Webhook）。
文档：https://developer.work.weixin.qq.com/document/path/99110
"""
from src.notify.webhook import WebhookNotifier
from src.types import WechatWebhookConfig
from src.utils.logger import logger


def _truncate_utf8(text: str, max_bytes: int) -> str:
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text
    return raw[:max_bytes].decode("utf-8", errors="ignore")


class WechatWebhookNotifier(WebhookNotifier):
    name = "Wechat"

    def __init__(self, config: WechatWebhookConfig):
        super().__init__(config)
        self.webhook_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send'
        self.key = config.get('key', '')

    def get_url(self, mask: bool = False) -> str:
        return f"{self.webhook_url}?key={'******-****-****-****-******' if mask else self.key}"

    def test(self):
        self._send_text("你好，准备好接受推荐了吗")

    def _do_send(self, data: dict, message: str):
        logger.info(f"推送 [Wechat] 通知，地址为：{self.get_url(True)}")
        # markdown_v2 的 webhook 约束为 4096 bytes
        content = _truncate_utf8(message, 4096)
        self._send_markdown(content)

    def _send_text(self, content: str):
        payload = {
            "msgtype": "text",
            "text": {
                "content": content,
            },
        }
        self._post(payload)

    def _send_markdown(self, content: str):
        payload = {
            "msgtype": 'markdown_v2',
            "markdown_v2": {
                "content": content,
            },
        }
        self._post(payload)

    def _post(self, payload: dict):
        url = self.get_url()
        if not url:
            raise ValueError("Wechat webhook url 不能为空")

        resp = self._post_json(url, payload)

        # webhook 返回 JSON：{errcode:0, errmsg:'ok'}
        try:
            data = resp.json()
        except Exception:
            logger.error(f"[Wechat] 响应非 JSON: status={resp.status_code}, body={resp.text[:200]}")
            return

        errcode = data.get("errcode")
        if errcode not in (0, "0", None):
            logger.error(f"[Wechat] 推送失败: errcode={errcode}, errmsg={data.get('errmsg')}")
