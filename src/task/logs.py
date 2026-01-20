import os
import re
from datetime import datetime
from typing import List, Optional

from src.env import LOGS_DIR
from src.types import TaskLogEntry
from src.utils.logger import logger

_LOG_LINE_PATTERN = re.compile(r'^\[([^]]+)] \[([^]]+)] (.+)$')


def get_logs_file_name(task_id: int) -> str:
    return os.path.join(LOGS_DIR, f'task_{task_id}.log')


def remove_logs_file(task_id: int):
    filename = get_logs_file_name(task_id)
    if os.path.exists(filename):
        os.remove(filename)


def parse_log_line(line: str, task_id: int) -> Optional[TaskLogEntry]:
    """
    解析日志行，提取时间戳、日志级别和消息

    日志格式示例: [2026-01-19 16:41:52] [提示] 配置加载成功: data/app.config
    """
    line = line.strip()
    if not line:
        return None

    match = _LOG_LINE_PATTERN.match(line)
    if not match:
        return None

    timestamp, level, message = match.groups()
    return TaskLogEntry(
        id=0,
        timestamp=timestamp,
        level=level,
        message=message,
        task_id=task_id,
    )


async def get_task_logs(
        task_id: int,
        from_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        level_filter: Optional[List[str]] = None
) -> List[TaskLogEntry]:
    """
    从指定时间点之后获取日志（最多 limit 条）

    Args:
        task_id: 任务ID
        from_time: 起始时间（不包含该时间点）
        limit: 返回条数上限，None 表示不限制
        level_filter: 日志级别过滤

    Returns:
        List[TaskLogEntry]
    """
    filename = get_logs_file_name(task_id)
    logs: List[TaskLogEntry] = []

    if not os.path.exists(filename):
        return logs

    level_set = set(level_filter) if level_filter else None

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for log_id, line in enumerate(f, start=1):
                log_entry = parse_log_line(line, task_id)
                if log_entry is None:
                    continue

                if level_set and log_entry.get('level') not in level_set:
                    continue

                if from_time is not None:
                    try:
                        log_time = datetime.strptime(
                            log_entry.get('timestamp'),
                            "%Y-%m-%d %H:%M:%S"
                        )
                    except ValueError:
                        continue

                    if log_time <= from_time:
                        continue

                log_entry['id'] = log_id
                logs.append(log_entry)

                if limit is not None and len(logs) >= limit:
                    break

    except Exception as e:
        logger.error(f"读取任务日志失败: {e}")

    return logs
