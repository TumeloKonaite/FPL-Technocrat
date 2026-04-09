from pydantic import BaseModel

class VideoAnalysisJob(BaseModel):
    expert_name: str
    video_title: str
    published_at: str
    gameweek: int
    transcript: str | None = None
    video_url: str | None = None