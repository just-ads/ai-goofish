import asyncio
import random


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
