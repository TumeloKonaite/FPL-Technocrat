from pydantic import BaseModel, Field
from typing import Optional

class PlayerPick(BaseModel):
    player_name: str
    team: Optional[str] = None
    category: str
    reason: str
    confidence: float = Field(ge=0, le=1)

class TransferMove(BaseModel):
    move_out: Optional[str] = None
    move_in: Optional[str] = None
    horizon: str
    reason: str
    confidence: float = Field(ge=0, le=1)

class CaptainChoice(BaseModel):
    player_name: str
    rank: int
    reason: str
    confidence: float = Field(ge=0, le=1)

class ExpertVideoAnalysis(BaseModel):
    expert_name: str
    video_title: str
    gameweek: int
    strategy_summary: list[str]
    fixture_insights: list[str]
    player_picks: list[PlayerPick]
    transfer_plan: list[TransferMove]
    captaincy: list[CaptainChoice]
    chip_strategy: list[str]
    risks: list[str]
    final_takeaways: list[str]