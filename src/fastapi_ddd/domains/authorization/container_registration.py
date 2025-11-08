import punq
from .repositories import (
    RoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    UserRoleRepository,
)
from .services import RoleService


def register(container: punq.Container):
    container.register(RoleRepository)
    container.register(PermissionRepository)
    container.register(RolePermissionRepository)
    container.register(UserRoleRepository)
    container.register(RoleService)
