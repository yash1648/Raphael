from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.workflow_engine import WorkflowEngine

router = APIRouter(tags=["workflows"])


@router.post("/workflows/continue/{project_id}")
def continue_project(project_id: int, db: Session = Depends(get_db)):
    engine = WorkflowEngine(db)
    return engine.continue_project(project_id)


@router.get("/workflows/summary/{project_id}")
def summarize_project(project_id: int, db: Session = Depends(get_db)):
    engine = WorkflowEngine(db)
    return engine.summarize_project(project_id)


@router.get("/workflows/review/{project_id}")
def review_project(project_id: int, db: Session = Depends(get_db)):
    engine = WorkflowEngine(db)
    return engine.review_project(project_id)
