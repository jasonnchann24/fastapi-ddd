from datetime import timedelta
from uuid import UUID
from fastapi_ddd.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from fastapi_ddd.core.config import settings
from fastapi import HTTPException, status

from fastapi_ddd.core.base.base_service import BaseService
from fastapi_ddd.core.security import hash_password
from .models import User
from .schemas import UserCreateSchema, UserUpdateSchema, UserBaseSchema
from .repositories import UserRepository


class UserService(BaseService[User, UserCreateSchema, UserCreateSchema]):
    """
    User business logic service.
    Handles validation, hashing and uniqueness.
    """

    def __init__(self, repository: UserRepository):
        super().__init__(repository)
        self.repository: UserRepository = repository

    def get_default_order_by(self):
        """Define default ordering for this service"""
        return User.created_at.desc()

    def get_searchable_fields(self) -> list[str]:
        """Define which fields can be searched"""
        return ["username", "email"]

    async def before_create(self, user_in: UserCreateSchema):
        # Check uniqueness
        is_unique, error_msg = await self.repository.check_unique(
            username=user_in.username, email=user_in.email
        )
        if not is_unique:
            raise HTTPException(status_code=409, detail=error_msg)

        return user_in

    async def before_update(self, user_id: int, user_in: UserUpdateSchema):
        await self.get(user_id)

        # Uniqueness check
        is_unique, error_msg = await self.repository.check_unique(
            username=user_in.username,
            email=user_in.email,
            exclude_id=user_id,
        )
        if not is_unique:
            raise HTTPException(status_code=409, detail=error_msg)

        if not user_in.password_hash:
            return UserBaseSchema(**user_in.model_dump())

        return user_in

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """
        Authenticate user by username/email and password
        """

        user = await self.repository.get_by_username_or_email(username)

        if not user:
            return None

        if user.deleted_at is not None:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def create_tokens_for_user(self, user: User) -> tuple[str, str]:
        """
        Generate access and refresh token pair for user
        Returns (access_token, refresh_token)
        """

        access_token_data = {"sub": str(user.id), "username": user.username}
        access_token_exp = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data=access_token_data, expires_delta=access_token_exp
        )

        refresh_token_data = {"sub": str(user.id)}
        refresh_token_exp = timedelta(days=settings.jwt_refresh_token_expire_days)
        refresh_token = create_refresh_token(
            data=refresh_token_data, expires_delta=refresh_token_exp
        )

        return access_token, refresh_token

    async def refresh_user_tokens(self, refresh_token: str) -> tuple[str, str]:
        """
        Validate refresh token and generate new token pair
        Returns new (access_token, refresh_token)
        """

        payload = decode_refresh_token(refresh_token)

        user_id = UUID(payload.get("sub"))

        user = await self.repository.get(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        if user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or invalid",
            )

        return await self.create_tokens_for_user(user)
