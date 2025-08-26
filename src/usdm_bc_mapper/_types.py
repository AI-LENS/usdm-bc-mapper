from typing import Literal

from pydantic import BaseModel, RootModel
from pydantic.types import PositiveInt


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


History = RootModel[list[Message]]


class CdiscBcSearch(BaseModel):
    type: Literal["CdiscBcSearch"] = "CdiscBcSearch"
    query: str
    k: int = 10


class FinalAnswer(BaseModel):
    type: Literal["FinalAnswer"] = "FinalAnswer"
    biomedical_concept_id: str
    confidence: PositiveInt


class NotFoundAnswer(BaseModel):
    type: Literal["NotFoundAnswer"] = "NotFoundAnswer"


class NciSearch(BaseModel):
    type: Literal["NciSearch"] = "NciSearch"
    hukka: str


class LLmResponse(BaseModel):
    analysis: str
    decision: CdiscBcSearch | FinalAnswer | NotFoundAnswer
