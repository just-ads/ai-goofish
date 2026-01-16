"""Model provider config management.

Persists provider configs in `provider.config`.
"""

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.model_provider.models import ProviderConfig
from src.utils.file_operator import FileOperator

PROVIDER_CONFIG_FILE = "provider.config"


class ProviderCreateModel(BaseModel):
    """Provider 创建模型"""

    name: str
    endpoint: str
    model: str
    api_key: Optional[str] = ""
    proxy: Optional[str] = ""
    headers: Optional[Dict[str, str]] = {"Authorization": "Bearer {key}", "Content-Type": "application/json"}
    body: Optional[Dict[str, Any]] = {"model": "{model}", "messages": "{messages}"}


class ProviderUpdateModel(BaseModel):
    """Provider 更新请求模型"""

    name: Optional[str] = None
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    proxy: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


async def get_provider_config(provider_id: str) -> Optional[ProviderConfig]:
    """从 provider.config 文件获取指定 Provider 配置。"""

    file_op = FileOperator(PROVIDER_CONFIG_FILE)

    data_str = await file_op.read()
    if not data_str:
        return None

    try:
        provider_dicts = json.loads(data_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"{PROVIDER_CONFIG_FILE} JSON格式错误: {e}")

    if not isinstance(provider_dicts, list):
        return None

    provider_dict = next(
        (item for item in provider_dicts if isinstance(item, dict) and item.get("id") == provider_id),
        None,
    )

    if not provider_dict:
        return None

    try:
        return ProviderConfig(**provider_dict)
    except Exception as e:
        raise ValueError(f"Provider配置解析失败: {e}")


async def get_all_providers() -> List[ProviderConfig]:
    """从 provider.config 文件获取所有 Provider 配置。"""

    file_op = FileOperator(PROVIDER_CONFIG_FILE)

    data_str = await file_op.read()
    if not data_str:
        return []

    try:
        provider_dicts = json.loads(data_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"{PROVIDER_CONFIG_FILE} JSON格式错误: {e}")

    if not isinstance(provider_dicts, list):
        return []

    providers: List[ProviderConfig] = []
    for provider_dict in provider_dicts:
        if not isinstance(provider_dict, dict):
            continue

        try:
            provider = ProviderConfig(**provider_dict)
            providers.append(provider)
        except Exception:
            # Skip invalid config
            continue

    return providers


async def add_provider_config(provider_config: ProviderCreateModel) -> ProviderConfig:
    """添加 Provider 配置到 provider.config 文件。"""

    file_op = FileOperator(PROVIDER_CONFIG_FILE)

    data_str = await file_op.read()
    data = json.loads(data_str) if data_str else []
    if not isinstance(data, list):
        data = []

    data.sort(key=lambda item: item["id"])

    provider_id = int(data[-1]["id"]) + 1 if data else 0

    provider_dict = provider_config.model_dump(exclude={"id"})
    provider_dict["id"] = str(provider_id)

    data.append(provider_dict)

    await file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return ProviderConfig(**provider_dict)


async def update_provider_config(provider_id: str, provider_update: ProviderUpdateModel) -> ProviderConfig:
    """更新 provider.config 文件中的 Provider 配置。"""

    file_op = FileOperator(PROVIDER_CONFIG_FILE)

    data_str = await file_op.read()
    data = json.loads(data_str) if data_str else []
    if not isinstance(data, list):
        data = []

    provider_index = next((i for i, item in enumerate(data) if item.get("id") == provider_id), -1)
    if provider_index == -1:
        raise ValueError(f"Provider ID {provider_id} 不存在")

    provider_dict = data[provider_index]
    provider_dict.update(provider_update.model_dump(exclude={"id"}))

    await file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    return ProviderConfig(**provider_dict)


async def remove_provider_config(provider_id: str) -> Optional[ProviderConfig]:
    """从 provider.config 文件删除 Provider 配置。"""

    file_op = FileOperator(PROVIDER_CONFIG_FILE)

    data_str = await file_op.read()
    data = json.loads(data_str) if data_str else []
    if not isinstance(data, list):
        data = []

    provider_index = next((i for i, item in enumerate(data) if item.get("id") == provider_id), -1)
    if provider_index == -1:
        return None

    removed_provider = data.pop(provider_index)

    await file_op.write(json.dumps(data, ensure_ascii=False, indent=2))

    try:
        return ProviderConfig(**removed_provider)
    except Exception:
        return None
