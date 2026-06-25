from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search import SearchResponse
from app.services.search import SearchService

router = APIRouter(tags=["search"])


@router.get("/projects/{project_id}/search", response_model=SearchResponse)
def search_project(project_id: int, q: str = Query(""), db: Session = Depends(get_db)):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    service = SearchService(db)
    return service.search(project_id, q.strip())
