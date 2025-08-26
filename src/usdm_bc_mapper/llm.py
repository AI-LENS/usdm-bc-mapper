from typing import Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from ._types import History
from .settings import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def llm[T: BaseModel](history: History, output_model: Type[T]) -> T:
    response = await client.responses.parse(
        model=settings.openai_model,
        input=[
            *history.model_dump(),
        ],
        text_format=output_model,
    )
    assert response.output_parsed is not None, "Failed to parse response from LLM"
    return response.output_parsed
