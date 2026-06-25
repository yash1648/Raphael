from sqlalchemy.orm import Session

from app.models import Session as SessionModel
from app.schemas.session import SessionCreate, SessionUpdate


class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, project_id: int, data: SessionCreate) -> SessionModel:
        session = SessionModel(
            project_id=project_id,
            goal=data.goal,
            summary=data.summary,
            actions_taken=data.actions_taken,
            unresolved_items=data.unresolved_items,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_sessions(self, project_id: int) -> list[SessionModel]:
        return self.db.query(SessionModel).filter(SessionModel.project_id == project_id).all()

    def get_session(self, session_id: int) -> SessionModel | None:
        return self.db.query(SessionModel).filter(SessionModel.id == session_id).first()

    def update_session(self, session_id: int, data: SessionUpdate) -> SessionModel | None:
        session = self.get_session(session_id)
        if not session:
            return None
        if data.goal is not None:
            session.goal = data.goal
        if data.summary is not None:
            session.summary = data.summary
        if data.actions_taken is not None:
            session.actions_taken = data.actions_taken
        if data.unresolved_items is not None:
            session.unresolved_items = data.unresolved_items
        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session_id: int) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        self.db.delete(session)
        self.db.commit()
        return True
