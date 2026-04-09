from __future__ import annotations

from pydantic import BaseModel, Field


class ConsensusItem(BaseModel):
    item: str
    mention_count: int = Field(ge=0)
    average_confidence: float = Field(ge=0, le=1)
    supporting_experts: list[str]


class TransferConsensusItem(BaseModel):
    player_name: str
    direction: str
    mention_count: int = Field(ge=0)
    average_confidence: float = Field(ge=0, le=1)
    supporting_experts: list[str]


class FixtureInsightConsensusItem(BaseModel):
    insight: str
    mention_count: int = Field(ge=0)
    supporting_experts: list[str]
