from uuid import UUID
from fastapi_ddd.core.base.base_service import BaseService
from fastapi import HTTPException, status
from .models import Role, Permission, UserRole, RolePermission
from .schemas import (
    RoleCreateSchema,
    RoleUpdateSchema,
    RoleReadSchema,
    PermissionCreateSchema,
    PermissionUpdateSchema,
    PermissionReadSchema,
    UserRoleCreateSchema,
    UserRoleUpdateSchema,
    UserRoleReadSchema,
    RoleWithPermissionsReadSchema,
)
from .repositories import (
    RoleRepository,
    PermissionRepository,
    UserRoleRepository,
    RolePermissionRepository,
)

# =================================
# PermissionService
# =================================


class PermissionService(
    BaseService[Permission, PermissionCreateSchema, PermissionUpdateSchema]
):
    def __init__(self, repository: PermissionRepository):
        super().__init__(repository)
        self.repository: PermissionRepository = repository

    def get_default_order_by(self):
        return Permission.resource.asc()

    def get_searchable_fields(self):
        return ["resource", "action", "description"]

    async def before_create(self, permission_in: PermissionCreateSchema):
        """Validate uniqueness before creating permission"""
        if await self.repository.exists(
            resource=permission_in.resource, action=permission_in.action
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Permission '{permission_in.resource}:{permission_in.action}' already exists",
            )
        return permission_in

    async def before_update(
        self, permission_id: UUID, permission_in: PermissionUpdateSchema
    ):
        """Validate uniqueness before updating permission"""
        await self.get(permission_id)

        if permission_in.resource and permission_in.action:
            if await self.repository.exists_excluding(
                permission_id,
                resource=permission_in.resource,
                action=permission_in.action,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Permission '{permission_in.resource}:{permission_in.action}' already exists",
                )
        return permission_in


# =================================
# RoleService
# =================================
class RoleService(BaseService[Role, RoleCreateSchema, RoleUpdateSchema]):
    def __init__(
        self,
        repository: RoleRepository,
        permission_repository: PermissionRepository,
        role_permission_repository: RolePermissionRepository,
        user_role_repository: UserRoleRepository,
    ):
        super().__init__(repository)
        self.repository: RoleRepository = repository
        self.permission_repository: PermissionRepository = permission_repository
        self.role_permission_repository: RolePermissionRepository = (
            role_permission_repository
        )
        self.user_role_repository: UserRoleRepository = user_role_repository

    def get_default_order_by(self):
        return Role.name.asc()

    def get_searchable_fields(self):
        return ["name", "description"]

    async def before_create(self, role_in: RoleCreateSchema):
        if await self.repository.exists(name=role_in.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with name '{role_in.name}' already exists",
            )
        return role_in

    async def before_update(self, role_id: UUID, role_in: RoleUpdateSchema):
        await self.get(role_id)

        if role_in.name:
            if await self.repository.exists_excluding(role_id, name=role_in.name):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role with name '{role_in.name}' already exists",
                )
        return role_in

    async def sync_permissions(
        self, role_id: UUID, permission_ids: list[UUID]
    ) -> RoleWithPermissionsReadSchema:
        """
        Sync permissions to a role by replacing all existing permissions.
        Uses differential sync: only adds/removes what changed.
        """
        role = await self.get(role_id)

        desired_permission_ids = set(permission_ids)

        # Validate all permissions exist
        if desired_permission_ids:
            found_permissions = await self.permission_repository.get_by_ids(
                list(desired_permission_ids)
            )
            if len(found_permissions) != len(desired_permission_ids):
                found_ids = {p.id for p in found_permissions}
                missing_ids = desired_permission_ids - found_ids
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Permissions not found: {missing_ids}",
                )

        # Get existing role-permission assignments
        existing_assignments = await self.role_permission_repository.get_by_role(
            role_id
        )
        existing_permission_ids = {rp.permission_id for rp in existing_assignments}

        # Calculate diff
        to_add = desired_permission_ids - existing_permission_ids
        to_remove = existing_permission_ids - desired_permission_ids

        # Remove permissions that are no longer needed
        if to_remove:
            assignments_to_delete = [
                rp for rp in existing_assignments if rp.permission_id in to_remove
            ]
            await self.role_permission_repository.delete_by_ids(
                [rp.id for rp in assignments_to_delete]
            )

        # Add new permissions
        if to_add:
            await self.role_permission_repository.bulk_create(role_id, list(to_add))

        # Get updated permissions and return
        permissions = await self.permission_repository.get_permissions_by_role(role_id)

        return RoleWithPermissionsReadSchema(
            **role.model_dump(),
            permissions=[PermissionReadSchema.model_validate(p) for p in permissions],
        )

    async def sync_user_to_roles(
        self, user_id: UUID, role_ids: list[UUID]
    ) -> list[UserRoleReadSchema]:
        """
        Assign multiple roles to a user
        """
        desired_role_ids = set(role_ids)

        if desired_role_ids:
            found_roles = await self.repository.get_by_ids(list(desired_role_ids))
            if len(found_roles) != len(desired_role_ids):
                found_ids = {r.id for r in found_roles}
                missing_ids = desired_role_ids - found_ids
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role not found:{missing_ids}",
                )

        existing_assignments = await self.user_role_repository.get_by_user(user_id)
        existing_role_ids = {ur.role_id for ur in existing_assignments}

        to_add = desired_role_ids - existing_role_ids
        to_remove = existing_role_ids - desired_role_ids

        if to_remove:
            assignments_to_delete = [
                ur for ur in existing_assignments if ur.role_id in to_remove
            ]
            await self.user_role_repository.delete_by_ids(
                [ur.id for ur in assignments_to_delete]
            )

        if to_add:
            await self.user_role_repository.bulk_create(user_id, list(to_add))

        all_assignments = await self.user_role_repository.get_by_user(user_id)
        return [UserRoleReadSchema.model_validate(ur) for ur in all_assignments]
