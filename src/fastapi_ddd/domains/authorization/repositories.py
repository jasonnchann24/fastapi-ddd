from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import delete

from fastapi_ddd.core.base.base_repository import BaseRepository
from .models import Role, Permission, UserRole, RolePermission


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Role)

    async def get_by_ids(self, role_ids: list[UUID]) -> list[Role]:
        q = select(Role).where(Role.id.in_(role_ids))
        result = await self.session.exec(q)
        return list(result.all())

    async def get_by_names(self, names: list[str]) -> list[Role]:
        q = select(Role).where(Role.name.in_(names))
        result = await self.session.exec(q)
        return list(result.all())


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Permission)

    async def get_permissions_by_role(self, role_id: UUID) -> list[Permission]:
        """Get all permissions for a specific role"""
        q = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        result = await self.session.exec(q)
        return list(result.all())

    async def get_by_ids(self, permission_ids: list[UUID]) -> list[Permission]:
        """Get multiple permissions by IDs in one query"""
        q = select(Permission).where(Permission.id.in_(permission_ids))
        result = await self.session.exec(q)
        return list(result.all())


class UserRoleRepository(BaseRepository[UserRole]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserRole)

    async def get_by_user(self, user_id: UUID) -> list[UserRole]:
        q = select(UserRole).where(UserRole.user.id == user_id)
        result = await self.session.exec(q)
        return list(result.all())

    async def bulk_create_for_user(self, user_id: UUID, role_ids: list[UUID]) -> None:
        user_roles = [
            UserRole(user_id=user_id, role_id=role_id) for role_id in role_ids
        ]

        self.session.add_all(user_roles)
        await self.session.flush()

    async def delete_by_ids(self, assignment_ids: list[UUID]) -> int:
        """
        Delete multiple user-role assignments by IDs.
        Returns count deleted.
        """
        if not assignment_ids:
            return 0

        stmt = delete(UserRole).where(UserRole.id.in_(assignment_ids))
        result = await self.session.exec(stmt)
        await self.session.flush()
        return result.rowcount


class RolePermissionRepository(BaseRepository[RolePermission]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RolePermission)

    async def get_by_role(self, role_id: UUID) -> list[RolePermission]:
        """Get all role-permission assignments for a specific role"""
        q = select(RolePermission).where(RolePermission.role_id == role_id)
        result = await self.session.exec(q)
        return list(result.all())

    async def delete_by_role(self, role_id: UUID) -> int:
        """
        Delete all role-permission assignments for a specific role.
        Returns count deleted.
        """
        stmt = delete(RolePermission).where(RolePermission.role_id == role_id)
        result = await self.session.exec(stmt)
        await self.session.flush()
        return result.rowcount

    async def delete_by_ids(self, assignment_ids: list[UUID]) -> int:
        """
        Delete multiple role-permission assignments by IDs.
        Returns count deleted.
        """
        if not assignment_ids:
            return 0

        stmt = delete(RolePermission).where(RolePermission.id.in_(assignment_ids))
        result = await self.session.exec(stmt)
        await self.session.flush()
        return result.rowcount

    async def bulk_create(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        """
        Bulk create role-permission assignments.
        """
        role_permissions = [
            RolePermission(role_id=role_id, permission_id=permission_id)
            for permission_id in permission_ids
        ]

        self.session.add_all(role_permissions)
        await self.session.flush()
