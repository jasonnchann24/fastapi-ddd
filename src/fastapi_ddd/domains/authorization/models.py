from uuid import UUID
from sqlmodel import Field, Column, UniqueConstraint
from sqlalchemy import String
from fastapi_ddd.core.base.base_model import BaseModel, TimestampMixin


class Permission(BaseModel, TimestampMixin, table=True):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )

    resource: str = Field(max_length=30, index=True)
    action: str = Field(max_length=30)
    description: str | None = Field(max_length=300)


class Role(BaseModel, TimestampMixin, table=True):
    __tablename__ = "roles"

    name: str = Field(unique=True, max_length=30)
    description: str | None = Field(default=None, max_length=300)
    is_active: bool = Field(default=True)


class UserRole(BaseModel, TimestampMixin, table=True):
    __tablename__ = "user_roles"

    user_id: UUID = Field(sa_column=Column(String(36), index=True, nullable=False))
    role_id: UUID = Field(foreign_key="roles.id", index=True)


class RolePermission(BaseModel, TimestampMixin, table=True):
    __tablename__ = "role_permissions"

    role_id: UUID = Field(foreign_key="roles.id", index=True)
    permission_id: UUID = Field(foreign_key="permissions.id", index=True)
