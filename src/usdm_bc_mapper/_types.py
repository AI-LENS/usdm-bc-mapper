from typing import Literal

from pydantic import BaseModel, Field, RootModel


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
    vlm_group_id: str
    confidence: int = Field(..., ge=0, le=100)


class NotFoundAnswer(BaseModel):
    type: Literal["NotFoundAnswer"] = "NotFoundAnswer"


class NciSearch(BaseModel):
    type: Literal["NciSearch"] = "NciSearch"
    hukka: str


class LLmResponse(BaseModel):
    analysis: str
    decision: CdiscBcSearch | FinalAnswer | NotFoundAnswer
