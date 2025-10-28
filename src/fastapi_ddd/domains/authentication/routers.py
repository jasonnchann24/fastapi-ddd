from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_ddd.core.database import get_session
from fastapi_ddd.core.base.base_router import create_crud_router
from fastapi_ddd.core.permissions import AllowAny, IsAdmin, IsAuthenticated
from .schemas import UserCreateSchema, UserReadSchema, UserUpdateSchema
from .services import UserService
from .repositories import UserRepository


def get_user_service(session: AsyncSession) -> UserService:
    repo = UserRepository(session=session)
    return UserService(repository=repo)


# CRUD router for users
users_router = create_crud_router(
    service_factory=get_user_service,
    create_schema=UserCreateSchema,
    read_schema=UserReadSchema,
    update_schema=UserUpdateSchema,
    prefix="/users",
    tags=["authentication users"],
    exclude_routes=["create"],
    permissions={
        # "create": [Depends(AllowAny())],  # Anyone can register
        # "read_list": [Depends(IsAuthenticated())],  # Only logged in users
        # "read_one": [Depends(IsAuthenticated())],  # Only logged in users
        # "update": [Depends(IsOwnerOrAdmin())],  # Owner or admin only
        # "delete": [Depends(CanDeleteUser())],  # Admin only (via permission)
    },
)

# Custom router for additional endpoints
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


@auth_router.post(
    "/register",
    response_model=UserReadSchema,
    status_code=201,
    dependencies=[Depends(AllowAny())],
)
async def register(
    user_in: UserCreateSchema, session: AsyncSession = Depends(get_session)
):
    """Register a new user (alias for POST /users)"""
    service = get_user_service(session)
    return await service.create(user_in)


@auth_router.post(
    "/login",
    dependencies=[Depends(AllowAny())],
)
async def login(
    username: str, password: str, session: AsyncSession = Depends(get_session)
):
    """Login user and return access token"""
    # TODO
    pass


@auth_router.get(
    "/me", response_model=UserReadSchema, dependencies=[Depends(IsAuthenticated())]
)
async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
):
    pass


# Export all routers from this domain
routers = [users_router, auth_router]
