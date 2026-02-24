import unittest
from unittest.mock import Mock, patch

from src.notify.gotify import GotifyNotifier
from src.notify.ntfy import NtfyNotifier
from src.notify.serverchan import ServerChanNotifier
from src.notify.wechat_service import WechatWebhookNotifier


def make_test_task_result():
    return {"爬取时间": "2026-02-24 15:30:54", "搜索关键字": "大疆无人机", "任务名称": "大疆无人机", "商品信息": {"商品ID": "1023510830016", "商品链接": "https://www.goofish.com/item?id=1023510830016&categoryId=126866698", "商品标题": "大疆无人机flip 双电普通控128g内存，最近刚刚续费随心", "商品描述": "大疆无人机flip 双电普通控128g内存，最近刚刚续费随心换，有的都有，南宁只面交，诚心要的可以货到付款", "商品图片列表": ["http://img.alicdn.com/bao/uploaded/i3/2200626104259/O1CN01JSOOo61hKfy6IpNGF_!!4611686018427381699-0-xy_item.jpg", "http://img.alicdn.com/bao/uploaded/i1/2200626104259/O1CN01UBVfCw1hKfy5iqWiE_!!4611686018427381699-0-xy_item.jpg", "http://img.alicdn.com/bao/uploaded/i4/2200626104259/O1CN01RDJFTX1hKfy6DKKS7_!!4611686018427381699-0-xy_item.jpg"], "浏览量": 11, "当前售价": "2000", "商品原价": "0", "想要人数": 0, "发货地区": "崇左", "发布时间": "2026-02-24 08:58:20"}, "卖家信息": {"卖家ID": 2200626104259, "卖家昵称": "tbNick_4di8v", "实名认证": "实人认证已通过", "回复间隔": "3小时", "二十四小时回复率": "100%", "注册天数": "来闲鱼5年10个月", "卖家个性签名": "", "卖家已出售商品": 15, "卖家好评数": 2, "卖家差评数": 0, "卖家个人描述": "暂无", "卖家信用": "卖家信用优秀"}, "分析结果": {"推荐度": 75, "建议": "建议购买", "原因": "商品为大疆无人机Flip型号，配置齐全（双电、普通控、128g内存），图片真实，卖家信用良好。但描述未明确突出性价比，且面交限制在南宁，可能影响适用范围。整体匹配需求，但性价比和地域限制是主要扣分点。"}}


class NotifyTestCase(unittest.TestCase):
    def test_ntfy_send(self):
        notifier = NtfyNotifier({"type": "ntfy", "url": "https://ntfy.sh/test"})
        task_result = make_test_task_result()
        notifier.send(task_result)

    def test_gotify_send(self):
        notifier = GotifyNotifier({"type": "gotify", "url": "http://127.0.0.1", "token": "abc"})
        task_result = make_test_task_result()
        notifier.send(task_result)

    def test_wecom_webhook_send(self):
        notifier = WechatWebhookNotifier({"type": "wechat", "url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send", "key": "1d9d1a25-4247-48ca-bd0b-0f6a34ac2e0c"})
        task_result = make_test_task_result()
        notifier.send(task_result)

    def test_serverchan_send(self):
        notifier = ServerChanNotifier({"type": "serverchan", "sendkey": "SCT316072TSZwabrNOnUBvRkME01IyA4Q1"})
        task_result = make_test_task_result()
        notifier.send(task_result)


if __name__ == "__main__":
    unittest.main()
