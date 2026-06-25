from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    goal: str
    summary: str = ""
    actions_taken: str = ""
    unresolved_items: str = ""


class SessionUpdate(BaseModel):
    goal: str | None = None
    summary: str | None = None
    actions_taken: str | None = None
    unresolved_items: str | None = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    goal: str
    summary: str
    actions_taken: str
    unresolved_items: str
    created_at: datetime
