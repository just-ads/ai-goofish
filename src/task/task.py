import json

from typing import Optional, List, TypedDict
from pydantic import BaseModel
from src.config import TASKS_FILE
from src.task.result import remove_task_result
from src.utils.file_operator import FileOperator


class Task(TypedDict):
    task_id: int
    task_name: str
    enabled: bool
    keyword: str
    cron: str
    description: str
    max_pages: int
    personal_only: bool
    min_price: str
    max_price: str


class TaskUpdate(BaseModel):
    task_id: int
    task_name: Optional[str] = None
    enabled: Optional[bool] = None
    keyword: Optional[str] = None
    cron: Optional[str] = None
    description: Optional[str] = None
    max_pages: Optional[int] = None
    personal_only: Optional[bool] = None
    min_price: Optional[str] = None
    max_price: Optional[str] = None


class TaskWithoutID(BaseModel):
    task_name: str
    enabled: bool
    keyword: str
    cron: str
    description: str
    max_pages: int
    personal_only: bool
    min_price: str
    max_price: str


async def add_task(task: TaskWithoutID) -> Task:
    task_dict = task.model_dump()

    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()
    data = json.loads(data_str) if data_str else []

    data.sort(key=lambda item: item['task_id'])

    task_id = data[-1]['task_id'] + 1 if data else 0

    task_dict['task_id'] = task_id

    data.append(task_dict)

    await task_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return task_dict


async def update_task(task_update: TaskUpdate) -> Task:
    task_update_dict = task_update.model_dump(exclude_none=True)
    task_id = task_update_dict['task_id']

    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()

    data = json.loads(data_str) if data_str else []

    task = next((it for it in data if it['task_id'] == task_id), None)

    if not task:
        raise Exception(f'{task_id}任务不存在')

    task.update(task_update_dict)

    await task_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return task


async def get_task(task_id: int) -> Optional[Task]:
    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()

    data = json.loads(data_str) if data_str else []

    task = next((it for it in data if it['task_id'] == task_id), None)

    return task


async def remove_task(task_id: int) -> Optional[Task]:
    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()

    data = json.loads(data_str) if data_str else []

    task_index = next((i for i, item in enumerate(data) if item['task_id'] == task_id), -1)

    if task_index == -1:
        return None

    removed_task = data.pop(task_index)

    if removed_task:
        remove_task_result(removed_task['keyword'])

    await task_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return removed_task


async def get_all_tasks() -> List[Task]:
    task_file_op = FileOperator(TASKS_FILE)
    data_str = await task_file_op.read()
    data = json.loads(data_str) if data_str else []
    return data
