from __future__ import annotations

from pydantic import BaseModel

from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.video_job import VideoAnalysisJob


class VideoAnalysisRunResult(BaseModel):
    job: VideoAnalysisJob
    success: bool
    analysis: ExpertVideoAnalysis | None = None
    error: str | None = None


class GameweekOrchestrationResult(BaseModel):
    results: list[VideoAnalysisRunResult]
