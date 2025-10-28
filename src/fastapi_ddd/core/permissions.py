from typing import Callable, Any
from fastapi import Request, HTTPException, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_ddd.core.database import get_session


class PermissionDependency:
    """
    Base class for permissions.

    Usage:
        class IsAuthenticated(PermissionDependency):
            async def has_permission(self, request: Request, **kwargs) -> bool:
                return request.user.is_authenticated

        @router.get("/protected", dependencies=[Depends(IsAuthenticated())])
        async def protected_route():
            pass
    """

    def __init__(self, error_message: str = "Permission denied."):
        self.error_message = error_message

    async def has_permission(
        self, request: Request, session: AsyncSession, **kwargs
    ) -> bool:
        """
        Override this method to implement the permission logic.
        """
        raise NotImplementedError("Subclasses must implement has_permission()")

    async def __call__(
        self, request: Request, session: AsyncSession = Depends(get_session)
    ):
        """Always called by FastAPI's Depends()"""
        if not await self.has_permission(request, session):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=self.error_message
            )


class AllowAny(PermissionDependency):
    """Public permission"""

    async def has_permission(
        self, request: Request, session: AsyncSession, **kwargs
    ) -> bool:
        return True


class IsAuthenticated(PermissionDependency):
    """Protected authenticated"""

    def __init__(self):
        super().__init__("Authentication required")

    async def has_permission(
        self, request: Request, session: AsyncSession, **kwargs
    ) -> bool:
        # TODO
        # return hasattr(request.state, "user") and request.state.user is not None
        return True


class IsAdmin(PermissionDependency):
    def __init__(self):
        super().__init__("Admin access only")

    async def has_permission(
        self, request: Request, session: AsyncSession, **kwargs
    ) -> bool:
        # TODO
        # return hasattr(request.state, "user") and request.state.user.role == "admin"
        return False


# Helper class to combine multiple permissions (AND)
class RequireAll:
    def __init__(self, *permissions: PermissionDependency):
        self.permissions = permissions

    async def __call__(
        self, request: Request, session: AsyncSession = Depends(get_session)
    ):
        for permission in self.permissions:
            if not await permission.has_permission(request, session):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=permission.error_message,
                )


# Helper class to combine multiple permissions (OR)
class RequireAny:
    def __init__(self, *permissions: PermissionDependency):
        self.permissions = permissions

    async def __call__(
        self, request: Request, session: AsyncSession = Depends(get_session)
    ):
        for permission in self.permissions:
            if await permission.has_permission(request, session):
                return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
