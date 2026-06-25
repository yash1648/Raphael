from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.models import Project
from app.services.decision_engine import DecisionEngine
from app.services.memory import MemoryService
from app.services.search import SearchService


class WorkflowEngine:
    def __init__(self, db: Session):
        self.db = db
        self.memory = MemoryService(db)
        self.search = SearchService(db)
        self.decisions = DecisionEngine()

    def _require_project(self, project_id: int) -> None:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    def _task_dicts(self, tasks) -> list[dict]:
        return jsonable_encoder(tasks)

    def continue_project(self, project_id: int) -> dict:
        self._require_project(project_id)

        summary = self.memory.get_project_summary(project_id)
        active_work = self.memory.get_active_work(project_id)

        active_work_dicts = {
            "blocked_tasks": self._task_dicts(active_work.get("blocked_tasks", [])),
            "in_progress_tasks": self._task_dicts(active_work.get("in_progress_tasks", [])),
            "latest_session": jsonable_encoder(active_work.get("latest_session")),
            "latest_artifact": jsonable_encoder(active_work.get("latest_artifact")),
        }

        health = self.decisions.project_health(summary)
        next_action = self.decisions.recommend_next_action(summary, active_work_dicts)

        return {
            "workflow": "continue_project",
            "project_summary": jsonable_encoder(summary),
            "active_work": jsonable_encoder(active_work),
            "health": health,
            "next_action": next_action,
        }

    def summarize_project(self, project_id: int) -> dict:
        self._require_project(project_id)

        context = self.memory.get_project_context(project_id)
        summary = self.memory.get_project_summary(project_id)

        return {
            "workflow": "summarize_project",
            "context": jsonable_encoder(context),
            "summary": jsonable_encoder(summary),
        }

    def review_project(self, project_id: int) -> dict:
        self._require_project(project_id)

        context = self.memory.get_project_context(project_id)
        summary = self.memory.get_project_summary(project_id)

        tasks = self._task_dicts(context["tasks"])
        health = self.decisions.project_health(summary)
        blocked = self.decisions.find_blockers(tasks)
        prioritized = self.decisions.prioritize_tasks(tasks)

        return {
            "workflow": "review_project",
            "health": health,
            "blocked_tasks": jsonable_encoder(blocked),
            "prioritized_tasks": jsonable_encoder(prioritized),
        }
