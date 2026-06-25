from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.artifact import ArtifactCreate, ArtifactResponse, ArtifactUpdate
from app.services.artifact import ArtifactService
from app.services.project import ProjectService

router = APIRouter(tags=["artifacts"])


@router.post("/projects/{project_id}/artifacts", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
def create_artifact(project_id: int, data: ArtifactCreate, db: Session = Depends(get_db)):
    project_service = ProjectService(db)
    if not project_service.get_by_id(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    service = ArtifactService(db)
    return service.create_artifact(project_id, data)


@router.get("/projects/{project_id}/artifacts", response_model=list[ArtifactResponse])
def list_artifacts(project_id: int, db: Session = Depends(get_db)):
    project_service = ProjectService(db)
    if not project_service.get_by_id(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    service = ArtifactService(db)
    return service.get_artifacts(project_id)


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: int, db: Session = Depends(get_db)):
    service = ArtifactService(db)
    artifact = service.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.put("/artifacts/{artifact_id}", response_model=ArtifactResponse)
def update_artifact(artifact_id: int, data: ArtifactUpdate, db: Session = Depends(get_db)):
    service = ArtifactService(db)
    artifact = service.update_artifact(artifact_id, data)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.delete("/artifacts/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(artifact_id: int, db: Session = Depends(get_db)):
    service = ArtifactService(db)
    if not service.delete_artifact(artifact_id):
        raise HTTPException(status_code=404, detail="Artifact not found")
