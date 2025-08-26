from typing import Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from usdm_bc_mapper._types import History

client = AsyncOpenAI()  # set OPENAI_API_KEY environment variable


async def llm[T: BaseModel](history: History, output_model: Type[T]) -> T:
    response = await client.responses.parse(
        model="gpt-5-mini",
        input=[
            *history.model_dump(),
        ],
        text_format=output_model,
    )
    assert response.output_parsed is not None, "Failed to parse response from LLM"
    return response.output_parsed
