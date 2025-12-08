import random
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.triggers.base import BaseTrigger


class RandomOffsetTrigger(BaseTrigger):
    """
    支持随机偏移的触发器
    可以在基础触发器的时间点前后随机偏移执行

    示例:
    # 每天9:00执行，前后随机30分钟
    trigger = RandomOffsetTrigger(
        base_trigger=CronTrigger(hour=9, minute=0),
        offset_seconds=1800
    )

    # 每隔1小时执行，前后随机10分钟
    trigger = RandomOffsetTrigger(
        base_trigger=IntervalTrigger(hours=1),
        offset_seconds=600
    )
    """

    __slots__ = ('base_trigger', 'offset_seconds', '_next_fire_time')

    def __init__(self, base_trigger: BaseTrigger, offset_seconds: int):
        """
        初始化随机偏移触发器

        Args:
            base_trigger: 基础触发器
            offset_seconds: 随机偏移的最大秒数（正负偏移）
        """
        if offset_seconds < 0:
            raise ValueError("offset_seconds must be non-negative")

        self.base_trigger = base_trigger
        self.offset_seconds = offset_seconds
        self._next_fire_time: Optional[datetime] = None

    def get_next_fire_time(self,
                           previous_fire_time: Optional[datetime],
                           now: datetime) -> Optional[datetime]:
        """
        计算下一次触发时间

        Args:
            previous_fire_time: 上一次触发时间
            now: 当前时间

        Returns:
            下一次触发时间，如果任务结束则返回None
        """

        if self._next_fire_time and self._next_fire_time > now:
            return self._next_fire_time

        base_next_time = self.base_trigger.get_next_fire_time(
            previous_fire_time,
            now
        )

        if base_next_time is None:
            return None

        random_offset = random.randint(-self.offset_seconds, self.offset_seconds)

        next_fire_time = base_next_time + timedelta(seconds=random_offset)

        if next_fire_time <= now:
            next_fire_time = base_next_time

        self._next_fire_time = next_fire_time

        return next_fire_time

    def __getstate__(self) -> dict:
        """
        序列化触发器

        Returns:
            序列化后的字典
        """
        return {
            'base_trigger': self.base_trigger,
            'offset_seconds': self.offset_seconds
        }

    def __setstate__(self, state: dict) -> None:
        """
        反序列化触发器

        Args:
            state: 序列化后的字典
        """
        self.base_trigger = state['base_trigger']
        self.offset_seconds = state['offset_seconds']
        self._next_fire_time = None

    def __str__(self) -> str:
        return f"RandomOffsetTrigger(base={self.base_trigger}, offset={self.offset_seconds}s)"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} (base={self.base_trigger}, offset={self.offset_seconds}s)>"


class RandomTimeRangeTrigger(BaseTrigger):
    """
    在指定时间范围内随机选择执行时间的触发器

    示例:
    # 每天在09:00-11:00之间随机执行
    trigger = RandomTimeRangeTrigger(
        start_time="09:00",
        end_time="11:00",
        base_trigger=CronTrigger(hour=0, minute=0)
    )

    # 每周一在09:00-17:00之间随机执行
    trigger = RandomTimeRangeTrigger(
        start_time="09:00",
        end_time="17:00",
        base_trigger=CronTrigger(day_of_week="mon")
    )
    """

    __slots__ = ('start_time', 'end_time', 'base_trigger', '_next_fire_time')

    def __init__(self,
                 start_time: str,
                 end_time: str,
                 base_trigger: BaseTrigger):
        """
        初始化随机时间范围触发器

        Args:
            start_time: 开始时间字符串，格式 "HH:MM" 或 "HH:MM:SS"
            end_time: 结束时间字符串，格式同上
            base_trigger: 基础周期触发器
        """
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)
        self.base_trigger = base_trigger
        self._next_fire_time: Optional[datetime] = None

        if self.start_time >= self.end_time:
            raise ValueError("start_time must be earlier than end_time")

    @staticmethod
    def _parse_time(time_str: str) -> timedelta:
        """
        解析时间字符串为timedelta

        Args:
            time_str: 时间字符串，如 "09:30" 或 "14:45:30"

        Returns:
            timedelta对象
        """
        parts = time_str.split(':')
        if len(parts) == 2:
            hours, minutes = map(int, parts)
            seconds = 0
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
        else:
            raise ValueError(f"Invalid time format: {time_str}")

        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    def get_next_fire_time(self,
                           previous_fire_time: Optional[datetime],
                           now: datetime) -> Optional[datetime]:
        """
        计算下一次触发时间
        """
        if self._next_fire_time and self._next_fire_time > now:
            return self._next_fire_time

        base_next_time = self.base_trigger.get_next_fire_time(
            previous_fire_time,
            now
        )

        if base_next_time is None:
            return None

        base_date = base_next_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        start_seconds = int(self.start_time.total_seconds())
        end_seconds = int(self.end_time.total_seconds())

        random_seconds = random.randint(start_seconds, end_seconds)

        next_fire_time = base_date + timedelta(seconds=random_seconds)

        while next_fire_time <= base_next_time:
            next_fire_time += timedelta(days=1)

        self._next_fire_time = next_fire_time

        return next_fire_time

    def __getstate__(self) -> dict:
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'base_trigger': self.base_trigger
        }

    def __setstate__(self, state: dict) -> None:
        self.start_time = state['start_time']
        self.end_time = state['end_time']
        self.base_trigger = state['base_trigger']
        self._next_fire_time = None

    def __str__(self) -> str:
        return (f"RandomTimeRangeTrigger(start={self.start_time}, "
                f"end={self.end_time}, base={self.base_trigger})")

    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__} "
                f"(start={self.start_time}, end={self.end_time}, "
                f"base={self.base_trigger})>")


class RandomIntervalTrigger(BaseTrigger):
    """
    随机间隔触发器
    在最小和最大间隔之间随机选择执行间隔

    示例:
    # 每隔30-90分钟随机执行一次
    trigger = RandomIntervalTrigger(
        min_interval=1800,  # 30分钟
        max_interval=5400   # 90分钟
    )
    """

    __slots__ = ('min_interval', 'max_interval', '_next_fire_time')

    def __init__(self, min_interval: int, max_interval: int):
        """
        初始化随机间隔触发器

        Args:
            min_interval: 最小间隔秒数
            max_interval: 最大间隔秒数
        """
        if min_interval < 0 or max_interval < 0:
            raise ValueError("Intervals must be non-negative")
        if min_interval > max_interval:
            raise ValueError("min_interval must be less than or equal to max_interval")

        self.min_interval = min_interval
        self.max_interval = max_interval
        self._next_fire_time: Optional[datetime] = None

    def get_next_fire_time(self,
                           previous_fire_time: Optional[datetime],
                           now: datetime) -> Optional[datetime]:
        """
        计算下一次触发时间
        """
        if previous_fire_time is None:
            next_time = now
        else:
            random_interval = random.randint(self.min_interval, self.max_interval)
            next_time = previous_fire_time + timedelta(seconds=random_interval)

            if next_time <= now:
                next_time = now + timedelta(seconds=random_interval)

        self._next_fire_time = next_time
        return next_time

    def __getstate__(self) -> dict:
        return {
            'min_interval': self.min_interval,
            'max_interval': self.max_interval
        }

    def __setstate__(self, state: dict) -> None:
        self.min_interval = state['min_interval']
        self.max_interval = state['max_interval']
        self._next_fire_time = None

    def __str__(self) -> str:
        return (f"RandomIntervalTrigger(min={self.min_interval}s, "
                f"max={self.max_interval}s)")

    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__} "
                f"(min={self.min_interval}s, max={self.max_interval}s)>")
