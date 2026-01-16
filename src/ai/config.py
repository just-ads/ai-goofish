"""AI config management.

Persists AI configs in `ai.config`.
"""

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.ai.models import AIConfig
from src.utils.file_operator import FileOperator

AI_CONFIG_FILE = "ai.config"


class AICreateModel(BaseModel):
    """AI 创建模型"""

    name: str
    endpoint: str
    model: str
    api_key: Optional[str] = ""
    proxy: Optional[str] = ""
    headers: Optional[Dict[str, str]] = {"Authorization": "Bearer {key}", "Content-Type": "application/json"}
    body: Optional[Dict[str, Any]] = {"model": "{model}", "messages": "{messages}"}


class AIUpdateModel(BaseModel):
    """AI 更新请求模型"""

    name: Optional[str] = None
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    proxy: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


async def get_ai_config(ai_id: str) -> Optional[AIConfig]:
    """从 ai.config 文件获取指定 AI 配置。"""

    file_op = FileOperator(AI_CONFIG_FILE)

    data_str = await file_op.read()
    if not data_str:
        return None

    try:
        ai_dicts = json.loads(data_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"{AI_CONFIG_FILE} JSON格式错误: {e}")

    if not isinstance(ai_dicts, list):
        return None

    ai_dict = next(
        (item for item in ai_dicts if isinstance(item, dict) and item.get("id") == ai_id),
        None,
    )

    if not ai_dict:
        return None

    try:
        return AIConfig(**ai_dict)
    except Exception as e:
        raise ValueError(f"AI配置解析失败: {e}")


async def get_all_ai_config() -> List[AIConfig]:
    """从 ai.config 文件获取所有 AI 配置。"""

    file_op = FileOperator(AI_CONFIG_FILE)

    data_str = await file_op.read()
    if not data_str:
        return []

    try:
        ai_dicts = json.loads(data_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"{AI_CONFIG_FILE} JSON格式错误: {e}")

    if not isinstance(ai_dicts, list):
        return []

    ais: List[AIConfig] = []
    for ai_dict in ai_dicts:
        if not isinstance(ai_dict, dict):
            continue

        try:
            ai = AIConfig(**ai_dict)
            ais.append(ai)
        except Exception:
            # Skip invalid config
            continue

    return ais


async def add_ai_config(ai_config: AICreateModel) -> AIConfig:
    """添加 AI 配置到 ai.config 文件。"""

    file_op = FileOperator(AI_CONFIG_FILE)

    data_str = await file_op.read()
    data = json.loads(data_str) if data_str else []
    if not isinstance(data, list):
        data = []

    data.sort(key=lambda item: item["id"])

    ai_id = int(data[-1]["id"]) + 1 if data else 0

    ai_dict = ai_config.model_dump(exclude={"id"})
    ai_dict["id"] = str(ai_id)

    data.append(ai_dict)

    await file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return AIConfig(**ai_dict)


async def update_ai_config(ai_id: str, ai_update: AIUpdateModel) -> AIConfig:
    """更新 ai.config 文件中的 AI 配置。"""

    file_op = FileOperator(AI_CONFIG_FILE)

    data_str = await file_op.read()
    data = json.loads(data_str) if data_str else []
    if not isinstance(data, list):
        data = []

    ai_index = next((i for i, item in enumerate(data) if item.get("id") == ai_id), -1)
    if ai_index == -1:
        raise ValueError(f"AI ID {ai_id} 不存在")

    ai_dict = data[ai_index]
    ai_dict.update(ai_update.model_dump(exclude={"id"}))

    await file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return AIConfig(**ai_dict)


async def remove_ai_config(ai_id: str) -> Optional[AIConfig]:
    """从 ai.config 文件删除 AI 配置。"""

    file_op = FileOperator(AI_CONFIG_FILE)

    data_str = await file_op.read()
    data = json.loads(data_str) if data_str else []
    if not isinstance(data, list):
        data = []

    ai_index = next((i for i, item in enumerate(data) if item.get("id") == ai_id), -1)
    if ai_index == -1:
        return None

    removed_ai = data.pop(ai_index)

    await file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    try:
        return AIConfig(**removed_ai)
    except Exception:
        return None
