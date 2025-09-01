import json

from typing import Optional, Dict

from src.config import TASKS_FILE
from src.utils.file_operator import FileOperator


class Task(Dict):
    task_name: str
    enabled: bool
    keyword: str
    description: str
    max_pages: int
    personal_only: bool
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    cron: Optional[str] = None
    is_running: Optional[bool] = False


class TaskUpdate(Dict):
    task_name: Optional[str] = None
    enabled: Optional[bool] = None
    keyword: Optional[str] = None
    description: Optional[str] = None
    max_pages: Optional[int] = None
    personal_only: Optional[bool] = None
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    cron: Optional[str] = None
    is_running: Optional[bool] = None


async def add_task(task: Task) -> int:
    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()
    data = json.loads(data_str) if data_str else []

    data.append(task)

    await task_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return len(data)


async def update_task(task_id: int, task: Task):
    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()

    if not data_str:
        raise Exception(f'{task_id}任务不存在')

    data = json.loads(data_str)

    if len(data) <= task_id:
        raise Exception(f'{task_id}任务不存在')

    data[task_id] = task

    await task_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))


async def get_task(task_id: int) -> Task | None:
    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()

    if not data_str:
        raise Exception(f'{task_id}任务不存在')

    data = json.loads(data_str)

    if len(data) <= task_id:
        raise Exception(f'{task_id}任务不存在')

    return data[task_id]


async def remove_task(task_id: int):
    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()

    if not data_str:
        return

    data = json.loads(data_str)

    if len(data) <= task_id:
        return

    data.pop(task_id)

    await task_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))


async def get_all_tasks() -> list[Task]:
    task_file_op = FileOperator(TASKS_FILE)
    data_str = await task_file_op.read()
    data = json.loads(data_str) if data_str else []
    return data
