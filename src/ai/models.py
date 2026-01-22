"""
AI models.

These types describe a AI provider configuration (endpoint, model name,
credentials, request templates, etc.).
"""

import json
import re
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator


class AIMessage(BaseModel):
    """AI消息模型"""
    role: str = Field(..., description="消息角色：system/user/assistant")
    content: str = Field(..., description="消息内容")

    @validator('role')
    def validate_role(cls, v):
        """验证角色"""
        valid_roles = ['system', 'user', 'assistant', 'function']
        if v not in valid_roles:
            raise ValueError(f"角色必须是以下之一: {valid_roles}")
        return v


class AIConfig(BaseModel):
    """
    AI 配置模型

    一个 AI 配置由以下部分组成：
    - id: 唯一标识符
    - name: 名称（用于显示）
    - endpoint: API端点URL
    - api_key: API密钥
    - model: 模型名称
    - proxy: 代理地址
    - headers: 请求头配置
    - body: 请求体配置
    """
    id: str = Field(..., description="AI配置唯一ID")
    name: str = Field(..., description="AI配置名称")
    endpoint: str = Field(..., description="API端点URL")
    api_key: str = Field(..., description="API密钥")
    model: str = Field(..., description="模型名称")
    proxy: Optional[str] = Field(None, description="代理地址")

    headers: Dict[str, str] = Field(
        {"Authorization": "Bearer {key}", "Content-Type": "application/json"},
        description="请求头配置，JSON对象"
    )

    body: Dict[str, Any] = Field(
        {"model": "{model}", "messages": "{messages}"},
        description="请求体配置，JSON对象"
    )

    @validator('endpoint')
    def validate_endpoint(cls, v):
        """验证端点URL"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("端点URL必须以 http:// 或 https:// 开头")
        return v.rstrip('/')

    def get_headers(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """获取渲染后的headers"""
        from src.utils.logger import logger

        if not self.headers:
            return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        context = context or {}
        headers_context = {
            "key": self.api_key,
            "model": self.model,
            **context
        }
        rendered_headers = self._render_dict_template(self.headers, headers_context)
        logger.debug(f"Rendered headers: {rendered_headers}")
        return rendered_headers

    def get_body(self, messages: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None) -> str:
        """获取渲染后的请求体"""
        from src.utils.logger import logger

        default_body = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        if not self.body:
            return json.dumps(default_body, ensure_ascii=False)

        context = context or {}
        body_context = {
            "key": self.api_key,
            "model": self.model,
            "messages": messages,
            **context
        }

        rendered_body = self._render_dict_template(self.body, body_context)

        logger.debug(f"Rendered body: {rendered_body}")

        try:
            return json.dumps(rendered_body, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to serialize body to JSON: {e}")
            return json.dumps(default_body, ensure_ascii=False)

    def _render_template(self, template: str, context: Dict[str, Any]) -> Any:
        """渲染模板字符串"""

        def replace_match(match):
            """替换匹配的回调函数"""
            key = match.group(1).strip()

            if key in context:
                value = context[key]
                if isinstance(value, (dict, list)):
                    return json.dumps(value, ensure_ascii=False)
                else:
                    return str(value)
            else:
                return match.group(0)

        pattern = re.compile(r'\{\s*([\w_]+)\s*}')
        return pattern.sub(replace_match, template)

    def _render_dict_template(self, data: Any, context: Dict[str, Any]) -> Any:
        """递归渲染字典/列表中的模板字符串"""
        if isinstance(data, dict):
            rendered = {}
            for key, value in data.items():
                rendered[key] = self._render_dict_template(value, context)
            return rendered
        elif isinstance(data, list):
            return [self._render_dict_template(item, context) for item in data]
        elif isinstance(data, str):
            if data.strip() == '{messages}':
                return context['messages']
            return self._render_template(data, context)
        else:
            return data


class AIResponse(BaseModel):
    """AI 响应模型"""
    success: bool = Field(..., description="请求是否成功")
    content: Optional[str] = Field(None, description="响应内容")
    error: Optional[str] = Field(None, description="错误信息")
    ai_id: Optional[str] = Field(None, description="使用的AI配置ID")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="原始响应数据")
    latency: Optional[float] = Field(None, description="请求延迟（秒）")

    @classmethod
    def success_response(
            cls,
            content: str,
            id: str,
            raw_response: Optional[Dict[str, Any]] = None,
            latency: Optional[float] = None
    ) -> "AIResponse":
        """创建成功响应"""
        return cls(
            success=True,
            content=content,
            ai_id=id,
            raw_response=raw_response,
            latency=latency,
            error=None
        )

    @classmethod
    def error_response(
            cls,
            error: str,
            id: Optional[str] = None
    ) -> "AIResponse":
        """创建错误响应"""
        return cls(
            success=False,
            error=error,
            ai_id=id,
            content=None,
            raw_response=None,
            latency=None
        )


class AIPresetTemplate(BaseModel):
    """AI 预设模板"""
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    endpoint: str = Field(..., description="API端点示例")
    api_key: str = Field(..., description="API密钥")
    model: str = Field(..., description="模型示例")
    headers: Dict[str, str] = Field(..., description="headers模板示例")
    body: Dict[str, Any] = Field(..., description="body模板示例")

    @classmethod
    def get_preset_templates(cls) -> List["AIPresetTemplate"]:
        """获取预设模板列表"""
        return [
            cls(
                id='1',
                name="OpenAI兼容API",
                description="支持OpenAI格式的API",
                endpoint="https://api.openai.com/v1/chat/completions",
                api_key='',
                model="gpt-3.5-turbo",
                headers={
                    "Authorization": "Bearer {key}",
                    "Content-Type": "application/json"
                },
                body={
                    "model": "{model}",
                    "messages": "{messages}",
                    "response_format": {"type": "json_object"},
                    "stream": False
                }
            ),
            cls(
                id='2',
                name="DeepSeek API",
                description="DeepSeek聊天API",
                endpoint="https://api.deepseek.com/chat/completions",
                api_key='',
                model="deepseek-chat",
                headers={
                    "Authorization": "Bearer {key}",
                    "Content-Type": "application/json"
                },
                body={
                    "model": "{model}",
                    "messages": "{messages}",
                    "stream": False
                }
            ),
            cls(
                id='3',
                name="智谱AI API",
                description="智谱AI GLM系列模型",
                endpoint="https://open.bigmodel.cn/api/paas/v4/chat/completions",
                api_key='',
                model="glm-4",
                headers={
                    "Authorization": "Bearer {key}",
                    "Content-Type": "application/json"
                },
                body={
                    "model": "{model}",
                    "messages": "{messages}",
                    "stream": False
                }
            ),
            cls(
                id='4',
                name='Qwen AI API',
                description='阿里通义千问系列模型',
                endpoint='https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
                api_key='',
                model='qwen3-max',
                headers={
                    "Authorization": "Bearer {key}",
                    "Content-Type": "application/json"
                },
                body={
                    "model": "{model}",
                    "messages": "{messages}",
                    "stream": False,
                    "enable_thinking": False
                }
            ),
            cls(
                id='5',
                name='MIMO API',
                description='小米系列模型',
                endpoint='https://api.xiaomimimo.com/v1/chat/completions',
                api_key='',
                model='mimo-v2-flash',
                headers={
                    "Authorization": "Bearer {key}",
                    "Content-Type": "application/json"
                },
                body={
                    "model": "{model}",
                    "messages": "{messages}",
                    "stream": False,
                    "thinking": {
                        "type": "disabled"
                    }
                }
            ),
            cls(
                id='6',
                name='Gemini API',
                description='Google Gemini 系列模型',
                endpoint='https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
                api_key='',
                model='gemini-3-flash-preview',
                headers={
                    "Authorization": "Bearer {key}",
                    "Content-Type": "application/json"
                },
                body={
                    "model": "{model}",
                    "messages": "{messages}",
                    "stream": False,
                }
            )
        ]
