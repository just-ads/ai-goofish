from typing import TypedDict, List, Optional


class Product(TypedDict, total=False):
    商品ID: str
    商品链接: str
    商品标题: str
    商品描述: str
    商品图片列表: Optional[List[str]]
    浏览量: int
    当前售价: str
    商品原价: str
    想要人数: int
    发货地区: str
    发布时间: str


class Seller(TypedDict, total=False):
    卖家ID: str
    卖家昵称: str
    实名认证: str
    回复间隔: str
    二十四小时回复率: str
    注册天数: str
    卖家个性签名: str
    卖家已出售商品: str
    卖家好评数: str
    卖家差评数: str
    卖家个人描述: str
    卖家信用: str


class Analysis(TypedDict, total=False):
    推荐度: int
    建议: str
    原因: str
