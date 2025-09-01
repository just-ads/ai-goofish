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
