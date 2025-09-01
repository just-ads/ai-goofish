import math
from datetime import datetime

from src.utils.utils import safe_get


def format_registration_days(total_days: int) -> str:
    """
    将总天数格式化为“X年Y个月”的字符串。
    """
    if not isinstance(total_days, int) or total_days <= 0:
        return '未知'

    days_in_year = 365.25
    days_in_month = days_in_year / 12

    years = math.floor(total_days / days_in_year)
    remaining_days = total_days - (years * days_in_year)
    months = round(remaining_days / days_in_month)

    if months == 12:
        years += 1
        months = 0

    if years > 0 and months > 0:
        return f"来闲鱼{years}年{months}个月"
    elif years > 0 and months == 0:
        return f"来闲鱼{years}年整"
    elif years == 0 and months > 0:
        return f"来闲鱼{months}个月"
    else:
        return "来闲鱼不足一个月"


def parse_page(data: dict):
    page_data = []
    items = safe_get(data, "data", "resultList", default=[])

    for item in items:
        main_data = safe_get(item, "data", "item", "main", "exContent", default={})
        click_params = safe_get(item, "data", "item", "main", "clickParam", "args", default={})

        title = safe_get(main_data, "title", default="未知标题")
        price_parts = safe_get(main_data, "price", default=[])
        price = "".join([str(p.get("text", "")) for p in price_parts if isinstance(p, dict)]).replace("当前价", "").strip() if isinstance(price_parts, list) else "价格异常"
        if "万" in price: price = f"¥{float(price.replace('¥', '').replace('万', '')) * 10000:.0f}"
        area = safe_get(main_data, "area", default="地区未知")
        raw_link = safe_get(item, "data", "item", "main", "targetUrl", default="")
        pub_time_ts = click_params.get("publishTime", "")
        item_id = safe_get(main_data, "itemId", default="未知ID")
        original_price = safe_get(main_data, "oriPrice", default="暂无")
        wants_count = safe_get(click_params, "wantNum", default='NaN')

        tags = []
        if safe_get(click_params, "tag") == "freeship":
            tags.append("包邮")
        r1_tags = safe_get(main_data, "fishTags", "r1", "tagList", default=[])
        for tag_item in r1_tags:
            content = safe_get(tag_item, "data", "content", default="")
            if "验货宝" in content:
                tags.append("验货宝")

        page_data.append({
            "商品标题": title,
            "当前售价": price,
            "商品原价": original_price,
            "想要人数": wants_count,
            "商品标签": tags,
            "发货地区": area,
            "商品链接": raw_link.replace("fleamarket://", "https://www.goofish.com/"),
            "发布时间": datetime.fromtimestamp(int(pub_time_ts) / 1000).strftime("%Y-%m-%d %H:%M") if pub_time_ts.isdigit() else "未知时间",
            "商品ID": item_id
        })

    return page_data


def pares_product_detail_and_seller_info(data: dict, base_data: dict):
    item_do = safe_get(data, 'data', 'itemDO', default={})
    # image_infos = safe_get(item_do, 'imageInfos', default=[])
    # if image_infos:
    #     all_image_urls = [img.get('url') for img in image_infos if img.get('url')]
    #     if all_image_urls:
    #         base_data['商品图片列表'] = all_image_urls
    #         base_data['商品主图链接'] = all_image_urls[0]
    base_data['浏览量'] = safe_get(item_do, 'browseCnt', default='-')
    base_data['商品描述'] = safe_get(item_do, 'desc', default='无')

    seller_do = safe_get(data, 'data', 'sellerDO', default={})
    seller_id = safe_get(seller_do, 'sellerId')
    seller_name = safe_get(seller_do, 'nick', default="")
    identity_tags = safe_get(seller_do, 'identityTags', default=[])
    auth = '未知'
    if identity_tags:
        auth = identity_tags[0]['text']
    reply_ratio_24h = safe_get(seller_do, 'replyRatio24h', default='未知')
    reply_interval = safe_get(seller_do, 'replyInterval', default='未知')
    # avg reply 30d long
    register_day = safe_get(seller_do, 'userRegDay')

    register = '未知'
    if register_day:
        register = format_registration_days(register_day)

    seller_info = {
        '卖家ID': seller_id,
        '卖家昵称': seller_name,
        '实名认证': auth,
        '回复间隔': reply_interval,
        '二十四小时回复率': reply_ratio_24h,
        '注册天数': register
    }

    return base_data, seller_info


def pares_seller_detail_info(data: dict, base_data: dict):
    module = safe_get(data, 'data', 'module', default={})
    base = safe_get(module, 'base')
    seller_introduction = safe_get(base, 'introduction', default='暂无')
    ylz_tags = safe_get(base, 'ylzTags', default=[])
    credit = '暂无'
    if ylz_tags:
        credit = safe_get(ylz_tags[0], 'text', default='暂无')

    base_data['卖家个人描述'] = seller_introduction
    base_data['卖家信用'] = credit

    return base_data
