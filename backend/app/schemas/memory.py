from datetime import datetime

from pydantic import BaseModel

from app.schemas.artifact import ArtifactResponse
from app.schemas.project import ProjectResponse
from app.schemas.session import SessionResponse
from app.schemas.task import TaskResponse


class ProjectContextResponse(BaseModel):
    project: ProjectResponse
    tasks: list[TaskResponse]
    recent_sessions: list[SessionResponse]
    recent_artifacts: list[ArtifactResponse]


class TaskCounts(BaseModel):
    todo: int = 0
    in_progress: int = 0
    blocked: int = 0
    completed: int = 0


class ProjectSummaryResponse(BaseModel):
    project_name: str
    task_counts: TaskCounts
    recent_goals: list[str]
    recent_artifacts: list[str]
    last_activity: str


class ActiveWorkResponse(BaseModel):
    in_progress_tasks: list[TaskResponse]
    blocked_tasks: list[TaskResponse]
    latest_session: SessionResponse | None = None
    latest_artifact: ArtifactResponse | None = None
