from fastapi import Request
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_ddd.core.permissions import PermissionDependency
from .repositories import UserRepository


class IsOwner(PermissionDependency):
    def __init__(self):
        super().__init__("You can only access your own resources")

    async def has_permission(self, request: Request, session: AsyncSession, **kwargs):
        path_params = request.path_params
        resource_user_id = path_params.get("id")

        if not resource_user_id:
            return False

        # Todo
        # current user id = request.state.user.id
        # return current user id == resource user id

        return True
