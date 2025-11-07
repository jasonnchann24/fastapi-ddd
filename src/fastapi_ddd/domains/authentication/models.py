from datetime import datetime
from sqlmodel import Field
from fastapi_ddd.core.base.base_model import BaseModel, TimestampMixin, SoftDeleteMixin


class User(BaseModel, TimestampMixin, SoftDeleteMixin, table=True):
    __tablename__ = "users"

    username: str = Field(unique=True, max_length=30)
    email: str = Field(unique=True, max_length=50)
    password_hash: str = Field(max_length=128)

    full_name: str | None = Field(default=None, max_length=100)
    is_active: bool = Field(default=True, index=True)
    is_email_verified: bool = Field(default=False)
    email_verified_at: datetime | None = Field(default=None)

    password_changed_at: datetime | None = Field(default=None)
