from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Artifact, Project, Session as SessionModel, Task
from app.schemas.artifact import ArtifactResponse
from app.schemas.search import SearchResponse
from app.schemas.session import SessionResponse
from app.schemas.task import TaskResponse


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def _project_or_404(self, project_id: int) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    def search(self, project_id: int, query: str) -> SearchResponse:
        self._project_or_404(project_id)

        pattern = f"%{query}%"

        tasks = (
            self.db.query(Task)
            .filter(
                Task.project_id == project_id,
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                ),
            )
            .order_by(Task.updated_at.desc())
            .all()
        )

        sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.project_id == project_id,
                or_(
                    SessionModel.goal.ilike(pattern),
                    SessionModel.summary.ilike(pattern),
                    SessionModel.actions_taken.ilike(pattern),
                    SessionModel.unresolved_items.ilike(pattern),
                ),
            )
            .order_by(SessionModel.created_at.desc())
            .all()
        )

        artifacts = (
            self.db.query(Artifact)
            .filter(
                Artifact.project_id == project_id,
                or_(
                    Artifact.title.ilike(pattern),
                    Artifact.content.ilike(pattern),
                ),
            )
            .order_by(Artifact.updated_at.desc())
            .all()
        )

        task_responses = [TaskResponse.model_validate(t) for t in tasks]
        session_responses = [SessionResponse.model_validate(s) for s in sessions]
        artifact_responses = [ArtifactResponse.model_validate(a) for a in artifacts]

        total = len(task_responses) + len(session_responses) + len(artifact_responses)

        return SearchResponse(
            tasks=task_responses,
            sessions=session_responses,
            artifacts=artifact_responses,
            total_results=total,
        )
