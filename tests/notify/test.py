import unittest

from src.notify.gotify import GotifyNotifier
from src.notify.ntfy import NtfyNotifier

test_data = {"爬取时间": "2025-10-16 15:51", "搜索关键字": "N150软路由", "任务名称": "N150软路由", "商品信息": {"商品标题": "全新现货康耐信N150旗舰版加强版n150精英版N150 双 m2双sata接口 四口2.5g网卡 软路由 4口2.5g交换机  工控机 桌面小主机  迷你主机 HTPC主机 4k小主机 办公小主机 详细参数看图   旗舰版机箱散热好 相比普通实惠版好太多  实惠版散热不好 便宜30不推荐购买 本机搭...", "当前售价": "¥739", "商品原价": "暂无", "想要人数": "0", "商品标签": [], "发货地区": "湖北", "商品链接": "https://www.goofish.com/item?id=986331716609&referPageArgs=N150%E8%BD%AF%E8%B7%AF%E7%94%B1&gulSource=search&extra=%7B%22labelIds%22%3A%22539%2C919%2C13%22%2C%22source%22%3A%227%22%7D&referPage=Page_xySearchResult&trackParamsJson=%7B%22item_id%22%3A%22986331716609%22%2C%22item_type%22%3A%22goods%22%2C%22superlink_g_source_rn%22%3A%22514ec2f7b394d84800feb9c879b214ff%22%2C%22index%22%3A%222%22%2C%22source%22%3A%227%22%2C%22search_from_page%22%3A%22pcSearch%22%2C%22search_id%22%3A%22b37dac86dc47e65ed97294cd2b702eca%22%2C%22q%22%3A%22N150%E8%BD%AF%E8%B7%AF%E7%94%B1%22%2C%22superlink_g_source_item_id%22%3A%22986331716609%22%2C%22superlink_g_source_page%22%3A%22from_search%22%2C%22page%22%3A%221%22%2C%22id%22%3A%22986331716609%22%2C%22rn%22%3A%22514ec2f7b394d84800feb9c879b214ff%22%7D", "发布时间": "2025-10-13 23:18", "商品ID": "986331716609", "商品图片列表": ["http://img.alicdn.com/bao/uploaded/i1/O1CN01zl1mpF1PJ9XYKthNb_!!4611686018427385995-53-fleamarket.heic", "http://img.alicdn.com/bao/uploaded/i1/O1CN01xMQhdE1PJ9XXupieD_!!4611686018427385995-53-fleamarket.heic", "http://img.alicdn.com/bao/uploaded/i2/O1CN01pYIvLr1PJ9XY21spY_!!4611686018427385995-53-fleamarket.heic", "http://img.alicdn.com/bao/uploaded/i3/O1CN01Y7PLR61PJ9XXSF0lw_!!4611686018427385995-53-fleamarket.heic", "http://img.alicdn.com/bao/uploaded/i2/O1CN01hLSBSg1PJ9XY214wo_!!4611686018427385995-53-fleamarket.heic", "http://img.alicdn.com/bao/uploaded/i3/O1CN019yw16e1PJ9XYDb5Dw_!!4611686018427385995-53-fleamarket.heic", "http://img.alicdn.com/bao/uploaded/i3/O1CN015WhghD1PJ9XYDZPFk_!!4611686018427385995-53-fleamarket.heic", "http://img.alicdn.com/bao/uploaded/i4/O1CN016Fl7C41PJ9XYDYXEL_!!4611686018427385995-53-fleamarket.heic"], "浏览量": 48, "商品描述": "全新现货康耐信N150旗舰版加强版n150精英版N150 双m2双sata接口 四口2.5g网卡 软路由 4口2.5g交换机  工控机 桌面小主机  迷你主机 HTPC主机 4k小主机 办公小主机 详细参数看图 \n\n旗舰版机箱散热好 相比普通实惠版好太多  实惠版散热不好 便宜30不推荐购买 本机搭配ddr4内存 性价比高 支持m2和sata 带usb3.0 Type-C tf卡接口 外接拓展方便 显示接口一应俱全 \n\n标价为n150准系统 不含其他  需要自己折腾  \n可选配双m2拓展板  内存 固态  整机发货  提供预装系统  到手即用\n\n全新升级  性能和核显比n100都强很多\n可选双盘机柜  做nas 软路由 实惠又美观\n\n整机配置 预装系统 到手即用 需要哪个滴滴 顺丰包邮 小白优选\n4G内存/32g硬盘\n8G内存/128G硬盘\n16G内存/256G硬盘\n16G内存/512G硬盘\n32G内存/512G硬盘\n32G内存/1TB硬盘\n\n\n低价跑量，言简意赅，硬件厂家康耐信保修一年！假一赔十，好评百分百，值得信赖！"}, "卖家信息": {"卖家ID": 860231819, "卖家昵称": "阿喵工作室", "实名认证": "实人认证已通过", "回复间隔": "10分钟", "二十四小时回复率": "96%", "注册天数": "来闲鱼8年3个月", "卖家个性签名": "☀畅网微控官方代理 点赞关注收藏  售后不迷路 ☀\n☀行业深耕十年 全职专业靠谱 好评99% 信用极好 ☀", "卖家已出售商品": 1385, "卖家好评数": 446, "卖家差评数": 3, "卖家个人描述": "☀畅网微控官方代理 点赞关注收藏  售后不迷路 ☀\n☀行业深耕十年 全职专业靠谱 好评99% 信用极好 ☀", "卖家信用": "卖家信用极好"}, "分析结果": {"推荐度": 88, "建议": "非常建议购买", "原因": "卖家‘阿喵工作室’具备长期高信用、高回复率和极低差评率，专业可靠，与商品描述中‘假一赔十’‘好评百分百’等承诺一致，增强了可信度。商品为康耐信N150旗舰版加强版，配置明确（双M.2、双SATA、四口2.5G网卡等），支持多种用途（软路由、NAS、HTPC等），且提供多种整机配置选项和预装系统服务，适合不同用户需求。商品强调散热优化、性能优于N100，并明确区分实惠版与旗舰版，信息透明。但商品‘想要人数’为0、浏览量仅48，可能反映市场热度较低或新品尚未积累关注；此外，商品标题冗长重复，存在轻微营销夸大倾向。综合来看，商品本身参数扎实、卖家可靠，但需注意是否为全新正品及实际性能表现。"}}


class SpiderTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_ntfy(self):
        ntfy = NtfyNotifier('https://ntfy.sh/ads')
        ntfy.send(test_data)

    async def test_gotify(self):
        gotify = GotifyNotifier('http://127.0.0.1', 'Ap8e46dVroQGuSw')
        gotify.send(test_data)

if __name__ == '__main__':
    unittest.main()
