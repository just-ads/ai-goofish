"""通用 Webhook 通知器。
支持自定义 URL、Headers 和消息模板。
"""
import json

import httpx

from src.notify.base import BaseNotifier
from src.utils.logger import logger


class WebhookNotifier(BaseNotifier):
    """通用 Webhook 通知器。

    通过 JSON POST 将消息推送到任意 Webhook 地址。
    支持自定义请求头（Headers），适用于需要鉴权或特殊头的场景。
    """
    name = "Webhook"

    def __init__(self, config: dict):
        super().__init__(config)
        self.webhook_url: str = config.get('url', '').rstrip('/')
        self.headers: dict = self._parse_headers(config.get('headers', ''))

    # ------------------------------------------------------------------
    # 公共方法
    # ------------------------------------------------------------------

    def test(self):
        payload = {"content": "你好，准备好接受推荐了吗"}
        self._post_json(self.webhook_url, payload)

    def _do_send(self, data: dict, message: str):
        logger.info(f"推送 [Webhook] 通知，地址为：{self.webhook_url}")
        payload = {
            "title": data.get("title", ""),
            "content": message,
            "link": data.get("link", ""),
            "score": data.get("score", ""),
        }
        self._post_json(self.webhook_url, payload)

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _post_json(self, url: str, payload: dict, timeout: int = 30) -> httpx.Response:
        """发送 JSON POST 请求，携带自定义 Headers。"""
        if not url:
            raise ValueError(f"{self.name} webhook url 不能为空")

        headers = {"Content-Type": "application/json", **self.headers}
        resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)

        if resp.status_code >= 400:
            logger.error(
                f"[{self.name}] 请求失败: status={resp.status_code}, body={resp.text[:200]}"
            )

        return resp

    @staticmethod
    def _parse_headers(raw: str) -> dict:
        """将用户输入的 JSON 字符串解析为 Headers 字典。

        为空或解析失败时返回空字典。
        """
        if not raw or not raw.strip():
            return {}
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"[Webhook] Headers 解析失败，已忽略: {raw[:100]}")
        return {}
