from typing import Iterable, Literal

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.config import BASE_URL, MODEL_NAME, SKIP_AI_ANALYSIS, API_KEY


class AiClient:
    def __init__(self, base_url: str, model_name: str, key: str):
        self.model_name = model_name
        self.agent = AsyncOpenAI(api_key=key, base_url=base_url)

    async def ask(self, message: Iterable[ChatCompletionMessageParam], response_format: Literal['text', 'json_schema', 'json_object'] = 'json_object') -> str:
        resp = await self.agent.chat.completions.create(
            model=self.model_name,
            response_format={"type": response_format},
            messages=message,
            temperature=0.2
        )
        return resp.choices[0].message.content


ai_client = AiClient(BASE_URL, MODEL_NAME, API_KEY) if not SKIP_AI_ANALYSIS else None
