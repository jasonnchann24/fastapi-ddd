from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_ddd.core.base.base_router import create_crud_router

from .services import RoleService, PermissionService
from .schemas import RoleCreateSchema, RoleUpdateSchema, RoleReadSchema
from fastapi_ddd.core.containers import resolve_with_session


def get_role_service(session: AsyncSession) -> RoleService:
    return resolve_with_session(RoleService, session)


roles_router = create_crud_router(
    service_class=RoleService,
    create_schema=RoleCreateSchema,
    read_schema=RoleReadSchema,
    update_schema=RoleUpdateSchema,
    prefix="/roles",
    tags=["authorization roles"],
    exclude_routes=["create", "update", "delete"],
    permissions={},
)

routers = [roles_router]
