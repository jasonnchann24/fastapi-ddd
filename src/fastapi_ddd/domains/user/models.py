from typing import Annotated

from sqlmodel import Field
from fastapi_ddd.core.base.base_model import BaseModel


class User(BaseModel, table=True):
    __tablename__ = "users"

    username: Annotated[str, Field(unique=True, max_length=30)]
    email: Annotated[str, Field(unique=True, max_length=50)]
    password_hash: Annotated[str, Field(max_length=128)]
