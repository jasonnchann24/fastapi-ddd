from fastapi import Request, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_ddd.core.permissions import PermissionDependency
from .repositories import UserRepository


class IsOwner(PermissionDependency):
    """Check if current user owns the resource"""

    def __init__(self, owner_field: str = "user_id"):
        super().__init__("You can only access your own resources")
        self.owner_field = owner_field

    async def has_permission(self, request: Request, session: AsyncSession, **kwargs):
        # Get current user from request state
        current_user = getattr(request.state, "user", None)
        if not current_user:
            return False

        # Get resource from kwargs
        resource = kwargs.get("resource")
        if not resource:
            return False

        # Check ownership
        owner_id = getattr(resource, self.owner_field, None)
        return owner_id == current_user.id
