from datetime import datetime
from typing import Union
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SoftDeleteMixin(SQLModel):
    deleted_at: datetime | None = Field(default=None, index=True)
