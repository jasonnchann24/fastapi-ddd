from typing import Union

from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    id: Union[int, None] = Field(default=None, primary_key=True)
