from typing import Annotated, Union

from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Union[int, None] = Field(default=None, primary_key=True)
    username: Annotated[str, Field(unique=True, max_length=30)]
    email: Annotated[str, Field(unique=True, max_length=50)]
    password_hash: Annotated[str, Field(max_length=128)]