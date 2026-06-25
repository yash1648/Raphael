from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from app.models import Artifact, Project, Session as SessionModel, Task
from app.schemas.artifact import ArtifactResponse
from app.schemas.project import ProjectResponse
from app.schemas.session import SessionResponse
from app.schemas.task import TaskResponse


class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def _project_or_404(self, project_id: int) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    def get_project_context(self, project_id: int) -> dict:
        project = self._project_or_404(project_id)

        tasks = (
            self.db.query(Task)
            .filter(Task.project_id == project_id)
            .order_by(Task.priority.desc(), Task.updated_at.desc())
            .all()
        )

        recent_sessions = (
            self.db.query(SessionModel)
            .filter(SessionModel.project_id == project_id)
            .order_by(SessionModel.created_at.desc())
            .limit(10)
            .all()
        )

        recent_artifacts = (
            self.db.query(Artifact)
            .filter(Artifact.project_id == project_id)
            .order_by(Artifact.created_at.desc())
            .limit(10)
            .all()
        )

        return {
            "project": ProjectResponse.model_validate(project),
            "tasks": [TaskResponse.model_validate(t) for t in tasks],
            "recent_sessions": [SessionResponse.model_validate(s) for s in recent_sessions],
            "recent_artifacts": [ArtifactResponse.model_validate(a) for a in recent_artifacts],
        }

    def get_project_summary(self, project_id: int) -> dict:
        project = self._project_or_404(project_id)

        task_counts = {
            "todo": 0,
            "in_progress": 0,
            "blocked": 0,
            "completed": 0,
        }
        for status, count in (
            self.db.query(Task.status, sqlfunc.count(Task.id))
            .filter(Task.project_id == project_id)
            .group_by(Task.status)
            .all()
        ):
            task_counts[status] = count

        recent_sessions = (
            self.db.query(SessionModel.goal)
            .filter(SessionModel.project_id == project_id)
            .order_by(SessionModel.created_at.desc())
            .limit(5)
            .all()
        )
        recent_goals = [s.goal for s in recent_sessions if s.goal]

        recent_artifacts = (
            self.db.query(Artifact.title)
            .filter(Artifact.project_id == project_id)
            .order_by(Artifact.created_at.desc())
            .limit(5)
            .all()
        )
        recent_artifact_titles = [a.title for a in recent_artifacts]

        timestamps = [
            row[0]
            for row in (
                self.db.query(sqlfunc.max(Task.updated_at)).filter(Task.project_id == project_id).union(
                    self.db.query(sqlfunc.max(SessionModel.created_at)).filter(SessionModel.project_id == project_id),
                    self.db.query(sqlfunc.max(Artifact.updated_at)).filter(Artifact.project_id == project_id),
                ).all()
            )
            if row[0]
        ]
        timestamps.append(project.updated_at)
        last_activity = max(timestamps)
        last_activity_str = last_activity.isoformat()

        return {
            "project_name": project.name,
            "task_counts": task_counts,
            "recent_goals": recent_goals,
            "recent_artifacts": recent_artifact_titles,
            "last_activity": last_activity_str,
        }

    def get_active_work(self, project_id: int) -> dict:
        self._project_or_404(project_id)

        in_progress_tasks = (
            self.db.query(Task)
            .filter(Task.project_id == project_id, Task.status == "in_progress")
            .order_by(Task.priority.desc(), Task.updated_at.desc())
            .all()
        )

        blocked_tasks = (
            self.db.query(Task)
            .filter(Task.project_id == project_id, Task.status == "blocked")
            .order_by(Task.priority.desc(), Task.updated_at.desc())
            .all()
        )

        latest_session = (
            self.db.query(SessionModel)
            .filter(SessionModel.project_id == project_id)
            .order_by(SessionModel.created_at.desc())
            .first()
        )

        latest_artifact = (
            self.db.query(Artifact)
            .filter(Artifact.project_id == project_id)
            .order_by(Artifact.created_at.desc())
            .first()
        )

        return {
            "in_progress_tasks": [TaskResponse.model_validate(t) for t in in_progress_tasks],
            "blocked_tasks": [TaskResponse.model_validate(t) for t in blocked_tasks],
            "latest_session": SessionResponse.model_validate(latest_session) if latest_session else None,
            "latest_artifact": ArtifactResponse.model_validate(latest_artifact) if latest_artifact else None,
        }
