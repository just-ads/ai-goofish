import json
import os

import aiofiles

output_dir = "jsonl"


def save_task_result(keyword: str, data_record: dict):
    """将一个包含商品和卖家信息的完整记录追加保存到 .jsonl 文件。"""
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{keyword.replace(' ', '_')}_full_data.jsonl")
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(data_record, ensure_ascii=False) + "\n")
        return True
    except IOError as e:
        print(f"写入文件 {filename} 出错: {e}")
        return False


def remove_task_result(keyword: str):
    filename = os.path.join(output_dir, f"{keyword.replace(' ', '_')}_full_data.jsonl")
    if os.path.exists(filename):
        os.remove(filename)


async def get_task_result(keyword: str, page: int, limit: int = 20, recommended_only: bool = False, sort_by: str = "crawl_time", order: str = "asce"):
    results = []
    filename = os.path.join(output_dir, f"{keyword.replace(' ', '_')}_full_data.jsonl")

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
            price_str = str(info.get("当前售价", "0")).replace("¥", "").replace(",", "").strip()
            try:
                return float(price_str)
            except (ValueError, TypeError):
                return 0.0
        else:
            return item.get("爬取时间", "")

    async with aiofiles.open(filename, 'r', encoding='utf-8') as f:
        async for line in f:
            record = json.loads(line)
            if recommended_only:
                if record.get("ai_analysis", {}).get("is_recommended") is True:
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
