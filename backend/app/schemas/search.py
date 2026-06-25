from pydantic import BaseModel

from app.schemas.artifact import ArtifactResponse
from app.schemas.session import SessionResponse
from app.schemas.task import TaskResponse


class SearchResponse(BaseModel):
    tasks: list[TaskResponse]
    sessions: list[SessionResponse]
    artifacts: list[ArtifactResponse]
    total_results: int
