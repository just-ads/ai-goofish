"""
Notifier配置管理
"""
import json
from typing import Optional, List, Dict

from src.env import NOTIFIER_CONFIG_FILE
from src.utils.file_operator import FileOperator


async def get_notifier_config(notifier_id: str) -> Optional[Dict]:
    """
    从notifier.config文件获取指定Notifier配置

    Args:
        notifier_id: Notifier ID

    Returns:
        Notifier配置对象或None
    """
    notifier_file_op = FileOperator(NOTIFIER_CONFIG_FILE)

    data_str = await notifier_file_op.read()
    if not data_str:
        return None

    try:
        notifiers = json.loads(data_str) if data_str else []
        notifier = next((item for item in notifiers if isinstance(item, dict) and item.get('id') == notifier_id), None)
        return notifier

    except json.JSONDecodeError as e:
        raise ValueError(f"notifier.config文件JSON格式错误: {e}")


async def get_all_notifiers() -> List[Dict]:
    """
    从notifier.config文件获取所有Notifier配置

    Returns:
        Notifier配置对象列表
    """
    notifier_file_op = FileOperator(NOTIFIER_CONFIG_FILE)

    data_str = await notifier_file_op.read()
    if not data_str:
        return []

    try:
        notifiers = json.loads(data_str) if data_str else []
        return notifiers

    except json.JSONDecodeError as e:
        raise ValueError(f"notifier.config文件JSON格式错误: {e}")


async def get_enabled_notifiers() -> List[Dict]:
    """
    从notifier.config文件获取启用的Notifier配置

    Returns:
        Notifier配置对象列表
    """
    notifiers = await get_all_notifiers()
    return [notifier for notifier in notifiers if notifier.get('enable', False)]


async def add_notifier_config(notifier_config: Dict) -> Dict:
    """
    添加Notifier配置到notifier.config文件

    Args:
        notifier_config: Notifier创建模型

    Returns:
        添加的Notifier配置对象
    """
    notifier_file_op = FileOperator(NOTIFIER_CONFIG_FILE)

    data_str = await notifier_file_op.read()
    data = json.loads(data_str) if data_str else []

    max_id = 0
    if data:
        try:
            max_id = max(int(item['id']) for item in data if item.get('id').isdigit())
        except (ValueError, TypeError):
            max_id = 0

    notifier_id = str(max_id + 1)

    notifier_config['id'] = notifier_id

    data.append(notifier_config)

    await notifier_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return notifier_config


async def update_notifier_config(notifier_id: str, notifier_update: Dict, exclude: set[str] = None) -> Dict:
    """
    更新notifier.config文件中的Notifier配置

    Args:
        notifier_id: 要更新的Notifier ID
        notifier_update: 更新的Notifier配置对象

    Returns:
        更新后的Notifier配置对象
    """
    notifier_file_op = FileOperator(NOTIFIER_CONFIG_FILE)

    data_str = await notifier_file_op.read()
    data = json.loads(data_str) if data_str else []

    notifier_index = next((i for i, item in enumerate(data) if item.get('id') == notifier_id), -1)

    if notifier_index == -1:
        raise ValueError(f"Notifier ID {notifier_id} 不存在")

    exclude = ({"id"} | exclude) if exclude else {"id"}

    for exclude_item in exclude:
        notifier_update.pop(exclude_item, None)

    notifier = data[notifier_index]
    notifier.update(notifier_update)

    await notifier_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return notifier


async def remove_notifier_config(notifier_id: str) -> Optional[Dict]:
    """
    从notifier.config文件删除Notifier配置

    Args:
        notifier_id: 要删除的Notifier ID

    Returns:
        删除的Notifier配置对象或None
    """
    notifier_file_op = FileOperator(NOTIFIER_CONFIG_FILE)

    data_str = await notifier_file_op.read()
    data = json.loads(data_str) if data_str else []

    notifier_index = next((i for i, item in enumerate(data) if item.get('id') == notifier_id), -1)

    if notifier_index == -1:
        return None

    removed_notifier = data.pop(notifier_index)

    await notifier_file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    try:
        return removed_notifier
    except Exception:
        return None
