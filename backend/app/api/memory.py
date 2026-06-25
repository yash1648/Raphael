from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.memory import ActiveWorkResponse, ProjectContextResponse, ProjectSummaryResponse
from app.services.memory import MemoryService

router = APIRouter(tags=["memory"])


@router.get("/projects/{project_id}/context", response_model=ProjectContextResponse)
def get_project_context(project_id: int, db: Session = Depends(get_db)):
    service = MemoryService(db)
    return service.get_project_context(project_id)


@router.get("/projects/{project_id}/summary", response_model=ProjectSummaryResponse)
def get_project_summary(project_id: int, db: Session = Depends(get_db)):
    service = MemoryService(db)
    return service.get_project_summary(project_id)


@router.get("/projects/{project_id}/active-work", response_model=ActiveWorkResponse)
def get_active_work(project_id: int, db: Session = Depends(get_db)):
    service = MemoryService(db)
    return service.get_active_work(project_id)
