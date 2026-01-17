import json
import os
from collections import defaultdict
from typing import Literal, Optional

import aiofiles

from src.types import TaskResultSortBy, TaskResultHistory, TaskResultPagination, TaskResult
from src.utils.utils import clean_price

output_dir = "jsonl"


def get_result_filename(keyword: str) -> str:
    return os.path.join(output_dir, f"{keyword.replace(' ', '_')}_full_data.jsonl")


def save_task_result(keyword: str, data_record: TaskResult):
    """将一个包含商品和卖家信息的完整记录追加保存到 .jsonl 文件。"""
    os.makedirs(output_dir, exist_ok=True)
    filename = get_result_filename(keyword)
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(data_record, ensure_ascii=False) + "\n")
        return True
    except IOError as e:
        print(f"写入文件 {filename} 出错: {e}")
        return False


def remove_task_result(keyword: str):
    filename = get_result_filename(keyword)
    if os.path.exists(filename):
        os.remove(filename)


async def get_task_result(
        keyword: str,
        page: int,
        limit: int = 20,
        recommended_only: Optional[bool] = False,
        sort_by: Optional[TaskResultSortBy] = "crawl_time",
        order: Optional[Literal['asce', 'desc']] = "asce") -> TaskResultPagination:
    results = []
    filename = get_result_filename(keyword)

    if not os.path.exists(filename):
        return {
            "total": 0,
            "page": page,
            "limit": limit,
            "items": []
        }

    def get_sort_key(item: dict):
        info = item.get("商品信息", {})
        if sort_by == "publish_time":
            return info.get("发布时间", "0000-00-00 00:00")
        elif sort_by == "price":
            return clean_price(info.get("当前售价", "0"))
        else:
            return item.get("爬取时间", "")

    async with aiofiles.open(filename, 'r', encoding='utf-8') as f:
        async for line in f:
            record = json.loads(line)
            if recommended_only:
                if record.get("分析结果", {}).get("推荐度") >= 60:
                    results.append(record)
            else:
                results.append(record)

    results.sort(key=get_sort_key, reverse=order == 'desc')

    total_items = len(results)
    start = (page - 1) * limit
    end = start + limit
    paginated_results = results[start:end]

    return {
        "total": total_items,
        "page": page,
        "limit": limit,
        "items": paginated_results
    }


async def get_product_history_info(keyword: str) -> TaskResultHistory:
    filename = get_result_filename(keyword)
    prices_by_time = defaultdict(list)
    ids = set()
    prices = []

    if not os.path.exists(filename):
        return {
            'processed': ids,
            'prices': prices,
        }

    async with aiofiles.open(filename, 'r', encoding='utf-8') as f:
        async for line in f:
            record = json.loads(line)
            product_id = record.get('商品信息', {}).get('商品ID', '')
            ids.add(product_id)
            if record.get('分析结果', {}).get('推荐度', 0) >= 30:
                time = record.get('爬取时间')
                price_str = record.get('商品信息', {}).get('当前售价', '0')
                price = clean_price(price_str)
                prices_by_time[time].append(price)

    for time, price_list in prices_by_time.items():
        if not price_list:
            continue
        price_list.sort()
        trimmed = price_list[1:-1] if len(price_list) > 2 else price_list
        avg_price = sum(trimmed) / len(trimmed)
        prices.append({'时间': time, '价格': f'￥{round(avg_price, 2)}'})

    prices.sort(key=lambda it: it.get('时间'))

    return {
        'processed': ids,
        'prices': prices,
    }
