from datetime import datetime
from zoneinfo import ZoneInfo

_zone_info = ZoneInfo("Asia/Shanghai")


def now():
    return datetime.now(_zone_info)


def now_timestamp():
    return now().timestamp()


def now_str():
    return now().strftime("%Y-%m-%d %H:%M:%S")
