from __future__ import annotations

from pydantic import BaseModel, Field

from src.schemas.aggregate_report import (
    ConsensusItem,
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
