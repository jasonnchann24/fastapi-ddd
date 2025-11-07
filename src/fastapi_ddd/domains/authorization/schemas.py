from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID

# ========================================
# Permission Schemas
# ========================================


class PermissionBaseSchema(BaseModel):
    resource: str = Field(max_length=30)
    action: str = Field(max_length=30)
    description: str | None = Field(max_length=300, default=None)


class PermissionCreateSchema(PermissionBaseSchema):
    pass


class PermissionUpdateSchema(PermissionBaseSchema):
    pass


class PermissionReadSchema(PermissionBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


# ========================================
# Role Schemas
# ========================================


class RoleBaseSchema(BaseModel):
    name: str = Field(max_length=30)
    description: str | None = Field(max_length=30, default=None)
    is_active: bool = Field(default=True)


class RoleCreateSchema(RoleBaseSchema):
    pass


class RoleUpdateSchema(RoleBaseSchema):
    pass


class RoleReadSchema(RoleBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


# ========================================
# UserRole Schemas
# ========================================


class UserRoleBaseSchema(BaseModel):
    user_id: UUID
    role_id: UUID


class UserRoleCreateSchema(UserRoleBaseSchema):
    pass


class UserRoleUpdateSchema(UserRoleBaseSchema):
    pass


class UserRoleReadSchema(UserRoleBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


# ========================================
# Enhanced Schemas
# ========================================
class RoleWithPermissionsReadSchema(RoleReadSchema):
    """Schema for role with all its permissions included"""

    permissions: list[PermissionReadSchema] = Field(default_factory=list)


class PermissionWithRolesSchema(PermissionReadSchema):
    """Schema for permission showing which roles have it"""

    roles: list[RoleReadSchema] = Field(default_factory=list)


class UserRolesDetailSchema(BaseModel):
    """Schema showing a user with all assigned roles and their permissions"""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    roles: list[RoleWithPermissionsReadSchema] = Field(default_factory=list)
