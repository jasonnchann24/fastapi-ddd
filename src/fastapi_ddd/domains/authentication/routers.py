from typing import Annotated
from fastapi import APIRouter, Depends, Request, status, Response, Cookie, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_ddd.core.containers import resolve_with_session
from fastapi_ddd.core.database import get_session
from fastapi_ddd.core.config import settings
from fastapi_ddd.core.base.base_router import create_crud_router
from fastapi_ddd.core.permissions import AllowAny, IsAdmin, IsAuthenticated
from .schemas import UserCreateSchema, UserReadSchema, UserUpdateSchema, TokenResponse
from .services import UserService
from .repositories import UserRepository
from .models import User
from .dependencies import get_current_user


# CRUD router for users
users_router = create_crud_router(
    service_class=UserService,
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(AllowAny())],
)
async def register(
    user_in: UserCreateSchema, session: AsyncSession = Depends(get_session)
):
    """Register a new user (alias for POST /users)"""
    service = resolve_with_session(UserService, session)
    result = await service.create(user_in)
    await session.commit()
    return result


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(AllowAny())],
)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
):
    """
    Login with username /email and password
    Returns access token and sets refresh token in HTTP-only cookie
    """
    service = resolve_with_session(UserService, session)

    user = await service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = await service.create_tokens_for_user(user=user)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.jwt_cookie_secure,
        samesite=settings.jwt_cookie_samesite,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        domain=settings.jwt_cookie_domain or None,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@auth_router.post(
    "/refresh", response_model=TokenResponse, dependencies=[Depends(AllowAny())]
)
async def refresh(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Refresh access token using refresh token from cookie.
    """

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid"
        )

    service = resolve_with_session(UserService, session)

    try:
        new_token, new_refresh = await service.refresh_user_tokens(
            refresh_token=refresh_token
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh"
        )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=settings.jwt_cookie_secure,
        samesite=settings.jwt_cookie_samesite,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        domain=settings.jwt_cookie_domain or None,
        path="/",
    )

    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@auth_router.post("/logout")
async def logout(
    response: Response, current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Logout current user.
    Clears refresh token cookie.
    """
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token", domain=settings.jwt_cookie_domain or None
    )

    return {"message": "Successfully logged out"}


@auth_router.get("/me", response_model=UserReadSchema)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current authenticated user"""
    return current_user


# Export all routers from this domain
routers = [users_router, auth_router]
