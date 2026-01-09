import json
from typing import Optional, List

from src.env import TASKS_FILE
from src.task.result import remove_task_result
from src.types import Task
from src.utils.file_operator import FileOperator


async def add_task(task: Task) -> Task:
    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()
    data = json.loads(data_str) if data_str else []

    data.sort(key=lambda item: item['task_id'])

    task_id = data[-1]['task_id'] + 1 if data else 0

    task['task_id'] = task_id

    data.append(task)

    await task_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return task_dict  # type: ignore[return-value]


async def update_task(task_update: Task) -> Task:
    task_id = task_update['task_id']

    task_file_op = FileOperator(TASKS_FILE)

    data_str = await task_file_op.read()

    data = json.loads(data_str) if data_str else []

    task = next((it for it in data if it['task_id'] == task_id), None)

    if not task:
        raise Exception(f'{task_id}任务不存在')

    task.update(task_update)

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
