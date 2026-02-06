import json
from typing import Literal

from src.env import TASKS_RECORD_FILE
from src.types import TaskRecord
from src.utils.file_operator import FileOperator


async def get_task_record(task_id: int) -> TaskRecord | None:
    record_file_op = FileOperator(TASKS_RECORD_FILE)

    data_str = await record_file_op.read()
    data = json.loads(data_str) if data_str else []

    return next((it for it in data if it['task_id'] == task_id), None)


async def add_task_record(task_id: int, runed: Literal['normal', 'abnormal', 'risk']) -> TaskRecord:
    record_file_op = FileOperator(TASKS_RECORD_FILE)

    data_str = await record_file_op.read()
    data = json.loads(data_str) if data_str else []

    record = next((it for it in data if it['task_id'] == task_id), None)
    need_append = record is None

    if need_append:
        record = TaskRecord(task_id=task_id, total_count=0, normal_count=0, abnormal_count=0, risk_count=0)

    record['total_count'] += 1
    if runed == 'normal':
        record['normal_count'] += 1
    if runed == 'abnormal':
        record['abnormal_count'] += 1
    if runed == 'risk':
        record['risk_count'] += 1

    if need_append:
        data.append(record)

    await record_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return record


async def remove_task_record(task_id: int) -> TaskRecord | None:
    record_file_op = FileOperator(TASKS_RECORD_FILE)
    data_str = await record_file_op.read()
    data = json.loads(data_str) if data_str else []

    record_index = next((i for i, item in enumerate(data) if item['task_id'] == task_id), -1)

    if record_index == -1:
        return None

    record = data.pop(record_index)

    await record_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return record
