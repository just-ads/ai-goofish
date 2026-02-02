import unittest
from unittest.mock import Mock, patch

from src.notify.gotify import GotifyNotifier
from src.notify.ntfy import NtfyNotifier
from src.notify.wechat_service import WechatWebhookNotifier


def make_test_task_result():
    return {
        "爬取时间": "2026-01-15 20:00",
        "搜索关键字": "软路由",
        "任务名称": "软路由",
        "商品信息": {
            "商品标题": "全新现货 N150 软路由 4*2.5G",
            "当前售价": "¥739",
            "商品原价": "¥999",
            "发货地区": "湖北",
            "商品链接": "https://www.goofish.com/item?id=123",
            "商品图片列表": ["http://img.example.com/1.jpg"],
        },
        "分析结果": {
            "推荐度": 80,
            "原因": "价格合理，卖家信誉较好。",
        },
    }


class NotifyTestCase(unittest.TestCase):
    def test_ntfy_send(self):
        notifier = NtfyNotifier({"type": "ntfy", "url": "https://ntfy.sh/test"})
        task_result = make_test_task_result()

        with patch("src.notify.ntfy.httpx.post") as post:
            post.return_value = Mock()
            notifier.send(task_result)

            self.assertEqual(post.call_count, 1)
            args, kwargs = post.call_args
            self.assertEqual(args[0], "https://ntfy.sh/test")
            self.assertIn("headers", kwargs)
            self.assertIn("Title", kwargs["headers"])
            self.assertIn("Attach", kwargs["headers"])
            self.assertIn("Actions", kwargs["headers"])

    def test_gotify_send(self):
        notifier = GotifyNotifier({"type": "gotify", "url": "http://127.0.0.1", "token": "abc"})
        task_result = make_test_task_result()

        with patch("src.notify.gotify.httpx.post") as post:
            post.return_value = Mock()
            notifier.send(task_result)

            self.assertEqual(post.call_count, 1)
            args, kwargs = post.call_args
            self.assertEqual(args[0], "http://127.0.0.1/message?token=abc")
            self.assertIn("json", kwargs)
            self.assertIn("title", kwargs["json"])
            self.assertIn("message", kwargs["json"])

    def test_wecom_webhook_send_markdown(self):
        notifier = WechatWebhookNotifier({"type": "wechat", "url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"})
        task_result = make_test_task_result()

        response = Mock()
        response.status_code = 200
        response.text = "{\"errcode\":0,\"errmsg\":\"ok\"}"
        response.json.return_value = {"errcode": 0, "errmsg": "ok"}

        with patch("src.notify.wechat_service.httpx.post") as post:
            post.return_value = response
            notifier.send(task_result)

            self.assertEqual(post.call_count, 1)
            args, kwargs = post.call_args
            self.assertEqual(args[0], "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx")
            self.assertIn("json", kwargs)
            self.assertEqual(kwargs["json"]["msgtype"], "markdown")
            self.assertIn("markdown", kwargs["json"])
            self.assertIn("查看商品", kwargs["json"]["markdown"]["content"])


if __name__ == "__main__":
    unittest.main()
