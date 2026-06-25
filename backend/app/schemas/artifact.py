from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

ALLOWED_TYPES = {"note", "summary", "architecture", "research", "design", "decision"}


class ArtifactCreate(BaseModel):
    type: str
    title: str
    content: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ALLOWED_TYPES:
            raise ValueError(f"Type must be one of {ALLOWED_TYPES}")
        return v


class ArtifactUpdate(BaseModel):
    type: str | None = None
    title: str | None = None
    content: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ALLOWED_TYPES:
            raise ValueError(f"Type must be one of {ALLOWED_TYPES}")
        return v


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    type: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
