from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ProjectCreate) -> Project:
        project = Project(name=data.name, description=data.description)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_all(self) -> list[Project]:
        return self.db.query(Project).all()

    def get_by_id(self, project_id: int) -> Project | None:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def update(self, project_id: int, data: ProjectUpdate) -> Project | None:
        project = self.get_by_id(project_id)
        if not project:
            return None
        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: int) -> bool:
        project = self.get_by_id(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True
