from typing import Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from ._types import History
from .settings import settings

# Assume providers is imported or defined elsewhere in the module


async def llm[T: BaseModel](history: History, schema: Type[T]) -> T:
    client = AsyncOpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
    response = await client.chat.completions.parse(
        model=settings.llm_model,
        messages=history.model_dump(),
        response_format=schema,
    )

    assert response.choices[0].message.parsed is not None, "Response parsing failed"
    return response.choices[0].message.parsed
