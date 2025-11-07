from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_ddd.core.base.base_router import create_crud_router

from .services import RoleService, PermissionService
from .repositories import (
    RoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    UserRoleRepository,
)
from .schemas import RoleCreateSchema, RoleUpdateSchema, RoleReadSchema


def get_role_service(session: AsyncSession) -> RoleService:
    role_repo = RoleRepository(session=session)
    permission_repo = PermissionRepository(session=session)
    role_permission_repo = RolePermissionRepository(session=session)
    user_role_repo = UserRoleRepository(session=session)

    return RoleService(
        repository=role_repo,
        permission_repository=permission_repo,
        role_permission_repository=role_permission_repo,
        user_role_repository=user_role_repo,
    )


roles_router = create_crud_router(
    service_factory=get_role_service,
    create_schema=RoleCreateSchema,
    read_schema=RoleReadSchema,
    update_schema=RoleUpdateSchema,
    prefix="/roles",
    tags=["authorization roles"],
    exclude_routes=["create", "update", "delete"],
    permissions={},
)

routers = [roles_router]
