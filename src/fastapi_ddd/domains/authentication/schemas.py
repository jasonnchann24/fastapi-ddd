from pydantic import BaseModel, ConfigDict
from fastapi_ddd.core.security import hash_password
from datetime import datetime
from pydantic import computed_field, Field, EmailStr


class UserBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    username: str = Field(max_length=30)
    email: EmailStr = Field(max_length=50)


class UserCreateSchema(UserBaseSchema):
    password: str 

    @computed_field
    @property
    def password_hash(self) -> str:
        return hash_password(self.password)
    
class UserUpdateSchema(UserBaseSchema):
    password: str | None = Field(default=None)

    @computed_field
    @property
    def password_hash(self) -> str | None:
        if self.password:
            return hash_password(self.password)
        return None


class UserReadSchema(UserBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
