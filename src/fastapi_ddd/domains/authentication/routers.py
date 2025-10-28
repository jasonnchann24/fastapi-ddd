from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_ddd.core.database import get_session
from fastapi_ddd.core.base.base_router import create_crud_router
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
)

# Custom router for additional endpoints
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


@auth_router.post("/register", response_model=UserReadSchema, status_code=201)
async def register(
    user_in: UserCreateSchema, session: AsyncSession = Depends(get_session)
):
    """Register a new user (alias for POST /users)"""
    service = get_user_service(session)
    return await service.create(user_in)


@auth_router.post("/login")
async def login(
    username: str, password: str, session: AsyncSession = Depends(get_session)
):
    """Login user and return access token"""
    # TODO
    pass


# Export all routers from this domain
routers = [users_router, auth_router]
