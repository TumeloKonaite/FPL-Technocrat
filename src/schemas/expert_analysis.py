from typing import Literal

from pydantic import BaseModel


class ExpertVideoAnalysis(BaseModel):
    expert_name: str
    video_title: str
    gameweek: int
    summary: str
    key_takeaways: list[str]
    recommended_players: list[str]
    avoid_players: list[str]
    captaincy_picks: list[str]
    chip_strategy: str | None = None
    reasoning: list[str]
    confidence: Literal["low", "medium", "high"]
