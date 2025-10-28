from sqlmodel import Field
from fastapi_ddd.core.base.base_model import BaseModel, TimestampMixin, SoftDeleteMixin


class User(BaseModel, TimestampMixin, SoftDeleteMixin, table=True):
    __tablename__ = "users"

    username: str = Field(unique=True, max_length=30)
    email: str = Field(unique=True, max_length=50)
    password_hash: str = Field(max_length=128)
