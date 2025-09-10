from typing import Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.usdm_bc_mapper._types import History
from src.usdm_bc_mapper.settings import settings

# Assume providers is imported or defined elsewhere in the module

# for OpenRouter Openai models

async def llm_OpenRouter[T: BaseModel](history: History, schema: Type[T]) -> T:
    client = AsyncOpenAI(
        base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key
    )
    response = await client.chat.completions.parse(
        model=settings.openrouter_model,
        messages=history.model_dump(),
        response_format=schema,
    )

    assert response.choices[0].message.parsed is not None, "Response parsing failed"
    return response.choices[0].message.parsed

# for OpenAI models

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def llm_OpenAi[T: BaseModel](history: History, output_model: Type[T]) -> T:
    response = await client.responses.parse(
        model=settings.openai_model,
        input=[
            *history.model_dump(),
        ],
        text_format=output_model,
    )
    assert response.output_parsed is not None, "Failed to parse response from LLM"
    return response.output_parsed