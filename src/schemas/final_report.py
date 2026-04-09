from __future__ import annotations

from pydantic import BaseModel, Field

from src.schemas.aggregate_report import (
    ConsensusItem,
    ConditionalAdviceItem,
    DisagreementReport,
    FixtureInsightConsensusItem,
    TransferConsensusItem,
)


class AggregatedFPLReport(BaseModel):
    gameweek: int | None = None
    expert_count: int = Field(ge=0)
    player_consensus: list[ConsensusItem]
    captaincy_consensus: list[ConsensusItem]
    transfer_consensus: list[TransferConsensusItem]
    fixture_insights: list[FixtureInsightConsensusItem]
    chip_strategy_consensus: list[ConsensusItem]
    disagreements: DisagreementReport
    conditional_advice: list[ConditionalAdviceItem]
    wait_for_news: list[str]


class FinalRecommendation(BaseModel):
    title: str
    rationale: str
    confidence: float | None = Field(default=None, ge=0, le=1)


class FinalDisagreement(BaseModel):
    topic: str
    summary: str
    sides: list[str] = Field(default_factory=list)


class FinalGameweekReport(BaseModel):
    gameweek: int | None = None
    overview: str
    transfers: list[FinalRecommendation] = Field(default_factory=list)
    captaincy: list[FinalRecommendation] = Field(default_factory=list)
    chip_strategy: list[FinalRecommendation] = Field(default_factory=list)
    fixture_notes: list[str] = Field(default_factory=list)
    disagreements: list[FinalDisagreement] = Field(default_factory=list)
    conditional_advice: list[str] = Field(default_factory=list)
    wait_for_news: list[str] = Field(default_factory=list)
    conclusion: str
