from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    domain: str

class ProjectOut(ProjectCreate):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
