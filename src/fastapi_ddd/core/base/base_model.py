from datetime import datetime
from typing import Union

from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    id: Union[int, None] = Field(default=None, primary_key=True)


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SoftDeleteMixin(SQLModel):
    deleted_at: datetime | None = Field(default=None)
