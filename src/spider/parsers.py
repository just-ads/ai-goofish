import math
from typing import Dict, Any

from src.types import Product, Seller
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


def pares_product_info_and_seller_info(
        data: Dict[str, Any],
        base_product_info: Dict[str, Any]
) -> tuple[Product, Seller]:
    item_do = safe_get(data, 'data', 'itemDO', default={})
    seller_do = safe_get(data, 'data', 'sellerDO', default={})

    image_infos = safe_get(item_do, 'imageInfos', default=[])
    all_image_urls = None
    if image_infos:
        all_image_urls = [img.get('url') for img in image_infos if img.get('url')]

    product_info: Product = {
        "商品ID": base_product_info.get('product_id', ''),
        "商品链接": base_product_info.get('product_url', ''),
        "商品标题": safe_get(item_do, 'title', default="未知标题"),
        "商品描述": safe_get(item_do, 'desc', default='无'),
        "商品图片列表": all_image_urls,
        "浏览量": safe_get(item_do, 'browseCnt', default='-'),
        "当前售价": safe_get(item_do, 'soldPrice', default='0'),
        "商品原价": safe_get(item_do, 'originalPrice', default='暂无'),
        "想要人数": safe_get(item_do, 'wantCnt', default=0),
        "发货地区": safe_get(seller_do, 'publishCity', default='未知'),
        "发布时间": safe_get(item_do, 'GMT_CREATE_DATE_KEY', default='未知时间'),
    }

    identity_tags = safe_get(seller_do, 'identityTags', default=[])
    auth = '未知'
    if identity_tags:
        auth = identity_tags[0]['text']
    # avg reply 30d long
    register_day = safe_get(seller_do, 'userRegDay')

    register = '未知'
    if register_day:
        register = format_registration_days(register_day)

    seller_info: Seller = {
        '卖家ID': safe_get(seller_do, 'sellerId'),
        '卖家昵称': safe_get(seller_do, 'nick', default=""),
        '实名认证': auth,
        '回复间隔': safe_get(seller_do, 'replyInterval', default='未知'),
        '二十四小时回复率': safe_get(seller_do, 'replyRatio24h', default='未知'),
        '注册天数': register,
        '卖家个性签名': safe_get(seller_do, 'signature', default=""),
        '卖家已出售商品': safe_get(seller_do, 'hasSoldNumInteger', default=0),
        '卖家好评数': safe_get(seller_do, 'remarkDO', 'sellerGoodRemarkCnt', default=0),
        '卖家差评数': safe_get(seller_do, 'remarkDO', 'sellerBadRemarkCnt', default=0),
    }

    return product_info, seller_info


def pares_seller_detail_info(data: Dict[str, Any], base_data: Seller) -> Seller:
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
