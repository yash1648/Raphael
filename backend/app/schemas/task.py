from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

ALLOWED_STATUSES = {"todo", "in_progress", "blocked", "completed"}


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "todo"
    priority: int = 0

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_STATUSES:
            raise ValueError(f"Status must be one of {ALLOWED_STATUSES}")
        return v


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: int | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ALLOWED_STATUSES:
            raise ValueError(f"Status must be one of {ALLOWED_STATUSES}")
        return v


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str
    status: str
    priority: int
    created_at: datetime
    updated_at: datetime
