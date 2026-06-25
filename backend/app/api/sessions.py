from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.session import SessionCreate, SessionResponse, SessionUpdate
from app.services.project import ProjectService
from app.services.session import SessionService

router = APIRouter(tags=["sessions"])


@router.post("/projects/{project_id}/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(project_id: int, data: SessionCreate, db: Session = Depends(get_db)):
    project_service = ProjectService(db)
    if not project_service.get_by_id(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    service = SessionService(db)
    return service.create_session(project_id, data)


@router.get("/projects/{project_id}/sessions", response_model=list[SessionResponse])
def list_sessions(project_id: int, db: Session = Depends(get_db)):
    project_service = ProjectService(db)
    if not project_service.get_by_id(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    service = SessionService(db)
    return service.get_sessions(project_id)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    service = SessionService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: int, data: SessionUpdate, db: Session = Depends(get_db)):
    service = SessionService(db)
    session = service.update_session(session_id, data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    service = SessionService(db)
    if not service.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
