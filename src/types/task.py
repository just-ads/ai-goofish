"""
任务相关类型定义
"""
from enum import Enum
from typing import TypedDict, Optional, List, Set

from src.types.product import Product, Seller, Analysis


class Task(TypedDict, total=False):
    """任务类型"""
    task_id: int
    task_name: str
    keyword: str
    max_pages: int
    enabled: bool
    cron: str
    description: str
    min_price: Optional[str]
    max_price: Optional[str]
    personal_only: Optional[bool]
    running: Optional[bool]

class TaskResult(TypedDict, total=False):
    任务名称: str
    搜索关键字: str
    爬取时间: str
    商品信息: Product
    卖家信息: Seller
    分析结果: Optional[Analysis]


class TaskResultPagination(TypedDict, total=False):
    total: int
    page: int
    limit: int
    items: List[TaskResult]


class TaskResultSortBy(str, Enum):
    CRAWL_TIME = 'crawl_time'
    PUBLISH_TIME = 'publish_time'
    PRICE = 'price'

class ProductPriceData(TypedDict):
    时间: str
    价格: str

class TaskResultHistory(TypedDict):
    processed: Set[int]
    prices: List[ProductPriceData]
