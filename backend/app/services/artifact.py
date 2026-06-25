from sqlalchemy.orm import Session

from app.models import Artifact
from app.schemas.artifact import ArtifactCreate, ArtifactUpdate


class ArtifactService:
    def __init__(self, db: Session):
        self.db = db

    def create_artifact(self, project_id: int, data: ArtifactCreate) -> Artifact:
        artifact = Artifact(
            project_id=project_id,
            type=data.type,
            title=data.title,
            content=data.content,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def get_artifacts(self, project_id: int) -> list[Artifact]:
        return self.db.query(Artifact).filter(Artifact.project_id == project_id).all()

    def get_artifact(self, artifact_id: int) -> Artifact | None:
        return self.db.query(Artifact).filter(Artifact.id == artifact_id).first()

    def update_artifact(self, artifact_id: int, data: ArtifactUpdate) -> Artifact | None:
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            return None
        if data.type is not None:
            artifact.type = data.type
        if data.title is not None:
            artifact.title = data.title
        if data.content is not None:
            artifact.content = data.content
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def delete_artifact(self, artifact_id: int) -> bool:
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            return False
        self.db.delete(artifact)
        self.db.commit()
        return True
