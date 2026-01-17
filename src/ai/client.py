"""Generic AI client.

Sends requests to a configured AI endpoint (OpenAI-compatible, etc.).
"""

import asyncio
import json
import time
import httpx
from typing import List, Dict, Any, Optional, Union

from src.ai.models import AIConfig, AIMessage, AIResponse
from src.utils.logger import logger


class AIClient:
    """通用 AI 客户端"""

    def __init__(self, config: AIConfig):
        """
        初始化 AI 客户端

        Args:
            config: AI 配置
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def _ensure_client(self) -> None:
        """确保HTTP客户端已创建"""
        if self._client is None:
            timeout = httpx.Timeout(30.0, connect=10.0)
            if self.config.proxy:
                self._client = httpx.AsyncClient(timeout=timeout, proxy=self.config.proxy)
            else:
                self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def ask(
            self,
            messages: Union[List[AIMessage], List[Dict[str, str]]],
            parameters: Optional[Dict[str, Any]] = None,
            context: Optional[Dict[str, Any]] = None,
            max_retries: int = 3
    ) -> AIResponse:
        """
        向 AI 服务发送请求

        Args:
            messages: 消息列表
            parameters: 覆盖默认参数
            context: 模板渲染上下文
            max_retries: 最大重试次数

        Returns:
            AI 响应
        """
        # 转换消息格式
        formatted_messages = self._format_messages(messages)

        # 准备请求参数
        request_params = parameters or {}

        # 发送请求（带重试）
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                response = await self._send_request(
                    messages=formatted_messages,
                    parameters=request_params,
                    context=context,
                    attempt=attempt + 1
                )

                latency = time.time() - start_time
                response.latency = latency

                if response.success:
                    logger.info(
                        f"AI请求成功: {self.config.name}, "
                        f"尝试次数: {attempt + 1}, 延迟: {latency:.2f}s"
                    )
                    return response
                else:
                    logger.warning(
                        f"AI请求失败: {self.config.name}, "
                        f"错误: {response.error}, 尝试次数: {attempt + 1}"
                    )

                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 指数退避
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(
                    f"AI请求异常: {self.config.name}, "
                    f"错误: {e}, 尝试次数: {attempt + 1}"
                )

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)

        return AIResponse.error_response(
            f"AI请求失败，已达到最大重试次数: {max_retries}",
            self.config.id
        )

    async def _send_request(
            self,
            messages: List[Dict[str, str]],
            parameters: Dict[str, Any],
            context: Optional[Dict[str, Any]],
            attempt: int
    ) -> AIResponse:
        """
        发送HTTP请求

        Args:
            messages: 消息列表
            parameters: 请求参数
            context: 模板渲染上下文
            attempt: 当前尝试次数

        Returns:
            AI 响应
        """
        await self._ensure_client()
        assert self._client is not None, "HTTP客户端未初始化"

        try:
            # 准备请求数据
            request_context = context or {}

            # 获取渲染后的headers和body
            headers = self.config.get_headers(request_context)
            body = self.config.get_body(messages, {**parameters, **request_context})

            # 构建请求URL
            request_url = self.config.endpoint

            # 发送请求
            logger.debug(
                f"发送AI请求: {self.config.name}, "
                f"URL: {request_url}, 尝试: {attempt}"
            )

            response = await self._client.post(
                request_url,
                headers=headers,
                content=body,
                timeout=30.0
            )

            # 解析响应
            return self._parse_response(response)

        except httpx.TimeoutException:
            return AIResponse.error_response("请求超时", self.config.id)
        except httpx.RequestError as e:
            return AIResponse.error_response(f"网络请求错误: {e}", self.config.id)
        except Exception as e:
            return AIResponse.error_response(f"请求处理错误: {e}", self.config.id)

    def _parse_response(self, response: httpx.Response) -> AIResponse:
        """
        解析HTTP响应

        Args:
            response: HTTP响应

        Returns:
            AI 响应
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            return AIResponse.error_response(
                f"响应JSON解析失败: {response.text[:200]}",
                self.config.id
            )

        # 检查HTTP状态码
        if response.status_code != 200:
            error_msg = self._extract_error_message(response_data, response.text)
            return AIResponse.error_response(
                f"HTTP {response.status_code}: {error_msg}",
                self.config.id
            )

        # 提取响应内容
        content = self._extract_content(response_data)

        if content is None:
            return AIResponse.error_response(
                f"无法从响应中提取内容: {response_data}",
                self.config.id
            )

        return AIResponse.success_response(
            content=content,
            id=self.config.id,
            raw_response=response_data
        )

    def _extract_error_message(self, response_data: Dict[str, Any], raw_text: str) -> str:
        """从响应数据中提取错误信息"""
        if isinstance(response_data, dict):
            # OpenAI格式错误
            if 'error' in response_data:
                error_obj = response_data['error']
                if isinstance(error_obj, dict) and 'message' in error_obj:
                    return error_obj['message']
                return str(error_obj)

            # 其他格式错误
            for key in ['message', 'error_message', 'err_msg']:
                if key in response_data:
                    return str(response_data[key])

        # 返回原始文本的前200个字符
        return raw_text[:200] if raw_text else "未知错误"

    def _extract_content(self, response_data: Dict[str, Any]) -> Optional[str]:
        """从响应数据中提取内容"""
        # 尝试不同API的响应格式

        # OpenAI格式: {"choices": [{"message": {"content": "..."}}]}
        if 'choices' in response_data and len(response_data['choices']) > 0:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
            elif 'text' in choice:
                return choice['text']

        # 嵌套的choices格式
        if 'data' in response_data and 'choices' in response_data['data']:
            choice = response_data['data']['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']

        # 直接包含result/content
        for key in ['result', 'content', 'text', 'output']:
            if key in response_data:
                content = response_data[key]
                if isinstance(content, str):
                    return content
                elif isinstance(content, dict) and 'content' in content:
                    return content['content']

        # 智谱AI格式: {"choices": [{"message": {"content": "..."}}]}
        if 'choices' in response_data:
            for choice in response_data['choices']:
                if isinstance(choice, dict) and 'message' in choice:
                    message = choice['message']
                    if isinstance(message, dict) and 'content' in message:
                        return message['content']

        return None

    def _format_messages(self, messages: Union[List[AIMessage], List[Dict[str, str]]]) -> List[Dict[str, str]]:
        """
        格式化消息列表

        Args:
            messages: 消息列表

        Returns:
            格式化后的消息字典列表
        """
        formatted_messages = []

        for msg in messages:
            if isinstance(msg, AIMessage):
                message_dict = msg.model_dump(exclude_none=True)
                formatted_messages.append(message_dict)
            elif isinstance(msg, dict):
                # 验证字典格式
                if 'role' not in msg or 'content' not in msg:
                    raise ValueError(f"消息字典必须包含role和content字段: {msg}")

                # 创建AIMessage进行验证
                agent_msg = AIMessage(**msg)
                formatted_messages.append(agent_msg.model_dump(exclude_none=True))
            else:
                raise ValueError(f"不支持的消息类型: {type(msg)}")

        return formatted_messages

    async def test_connection(self) -> bool:
        """
        测试 AI 连接

        Returns:
            连接是否成功
        """
        try:
            test_message = AIMessage(
                role="user",
                content="Hello, please respond with 'OK' if you can hear me."
            )

            response = await self.ask(
                messages=[test_message],
                max_retries=1
            )

            if response.success:
                logger.info(f"AI连接测试成功: {self.config.name}")
                return True
            else:
                logger.warning(f"AI连接测试失败: {self.config.name}, 错误: {response.error}")
                return False

        except Exception as e:
            logger.error(f"AI连接测试异常: {self.config.name}, 错误: {e}")
            return False
