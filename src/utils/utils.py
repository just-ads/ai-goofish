import asyncio
import random
import re

from typing import Optional, List, Dict


def get_id_by_url(url: str):
    import re
    match = re.search(r'[?&]id=(\d+)', url)
    return match.group(1) if match else None


async def random_sleep(min_seconds: float, max_seconds: float):
    delay = random.uniform(min_seconds, max_seconds)
    print(f"[延迟] 等待 {delay:.2f} 秒... (范围: {min_seconds}-{max_seconds}s)")
    await asyncio.sleep(delay)


def safe_get(data, *keys, default="暂无"):
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError, IndexError):
            return default
    return data


def clean_price(price_str: str) -> float:
    """提取价格数字"""
    try:
        return float(price_str.replace('¥', '').replace(',', '').strip())
    except (ValueError, TypeError):
        return 0.0


def dict_pick(src: dict, keys: list, default=None, strict=False) -> dict:
    """
    从字典中复制指定键对应的值。

    参数:
        src (dict): 原始字典
        keys (list): 需要复制的键列表
        default: 当键不存在时的默认值（仅在 strict=False 时生效）
        strict (bool): 若为 True，则键不存在会抛出 KeyError

    返回:
        dict: 仅包含指定键的新字典
    """
    if strict:
        # 严格模式：必须存在所有键
        return {k: src[k] for k in keys}
    else:
        # 宽松模式：不存在的键使用默认值
        return {k: src.get(k, default) for k in keys}


def extract_id_from_url_regex(url: str) -> Optional[str]:
    """
    使用正则表达式从URL中提取id参数

    Args:
        url (str): 要提取id的URL

    Returns:
        Optional[str]: 提取到的id，如果未找到则返回None
    """
    if not url or not isinstance(url, str):
        print(f"无效的URL输入: {url}")
        return None

    try:
        # 正则表达式匹配 id= 后面跟着的数字
        # 支持多种可能的格式：
        # 1. id=123456
        # 2. &id=123456
        # 3. ?id=123456
        # 4. id=123456& 或 id=123456? 或 id=123456
        pattern = r'(?:[?&]id=)(\d+)'
        match = re.search(pattern, url)

        if match:
            return match.group(1)
        else:
            print(f"URL中未找到id参数: {url}")
            return None
    except Exception as e:
        print(f"从URL提取id时发生错误: {url}, 错误: {e}")
        return None
