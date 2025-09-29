from typing import Iterable, Literal

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
import httpx

from src.config import OPENAI_BASE_URL, OPENAI_MODEL_NAME, SKIP_AI_ANALYSIS, OPENAI_API_KEY, OPENAI_EXTRA_BODY, OPENAI_PROXY_URL


class AiClient:
    def __init__(self, *, base_url: str, model_name: str, api_key: str, proxy: str = None, extra_body: str = None):
        self.model_name = model_name
        self.extra_body = extra_body
        http_client = None
        if proxy:
            http_client = httpx.AsyncClient(proxy=proxy)
        self.agent = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=http_client)

    async def ask(self, message: Iterable[ChatCompletionMessageParam], response_format: Literal['text', 'json_schema', 'json_object'] = 'json_object') -> str:
        resp = await self.agent.chat.completions.create(
            model=self.model_name,
            response_format={"type": response_format},
            messages=message,
            temperature=0.2,
            extra_body=self.extra_body
        )
        return resp.choices[0].message.content


ai_client = AiClient(
    base_url=OPENAI_BASE_URL,
    model_name=OPENAI_MODEL_NAME,
    api_key=OPENAI_API_KEY,
    proxy=OPENAI_PROXY_URL,
    extra_body=OPENAI_EXTRA_BODY
) if not SKIP_AI_ANALYSIS else None
