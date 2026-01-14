"""
Notifier配置模型
"""
from typing import Dict, Optional, Literal

from pydantic import BaseModel, Field, validator


class NotifierConfig(BaseModel):
    """
    Notifier配置模型

    一个Notifier由以下部分组成：
    - id: 唯一标识符
    - name: 名称（用于显示）
    - type: 通知类型（ntfy/gotify）
    - config: 具体的配置信息
    """
    id: str = Field(..., description="Notifier唯一ID")
    name: str = Field(..., description="Notifier名称")
    type: Literal["ntfy", "gotify"] = Field(..., description="Notifier类型")

    url: str = Field(..., description="通知服务URL")
    token: Optional[str] = Field(None, description="Gotify Token (仅gotify类型需要)")

    @validator('url')
    def validate_url(cls, v):
        """验证URL"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL必须以 http:// 或 https:// 开头")
        return v.rstrip('/')

    @validator('token')
    def validate_token(cls, v, values):
        """验证token（仅gotify需要）"""
        if values.get('type') == 'gotify' and not v:
            raise ValueError("Gotify类型必须提供token")
        return v

    def to_dict(self) -> Dict:
        """转换为字典格式（用于存储）"""
        data = self.model_dump()
        return data


class NotifierCreateModel(BaseModel):
    """Notifier创建模型"""
    name: str
    type: Literal["ntfy", "gotify"]
    url: str
    token: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "我的Ntfy",
                "type": "ntfy",
                "url": "https://ntfy.sh/mytopic"
            }
        }


class NotifierUpdateModel(BaseModel):
    """Notifier更新请求模型"""
    name: Optional[str] = None
    type: Optional[Literal["ntfy", "gotify"]] = None
    url: Optional[str] = None
    token: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "更新后的名称",
                "url": "https://ntfy.sh/newtopic"
            }
        }


class NotifierPresetTemplate(BaseModel):
    """Notifier预设模板"""
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    type: Literal["ntfy", "gotify"] = Field(..., description="Notifier类型")
    url: str = Field(..., description="URL示例")
    token: Optional[str] = Field(None, description="Token示例 (仅gotify)")

    @classmethod
    def get_preset_templates(cls) -> list["NotifierPresetTemplate"]:
        """获取预设模板列表（供前端选择）"""
        return [
            cls(
                id='1',
                name="Ntfy官方服务",
                description="使用Ntfy官方服务",
                type="ntfy",
                url="https://ntfy.sh/mytopic",
                token=None
            ),
            cls(
                id='2',
                name="Ntfy自建服务",
                description="使用自建的Ntfy服务",
                type="ntfy",
                url="http://localhost:8080/mytopic",
                token=None
            ),
            cls(
                id='3',
                name="Gotify自建服务",
                description="使用自建的Gotify服务",
                type="gotify",
                url="http://localhost:8080",
                token=""
            )
        ]
