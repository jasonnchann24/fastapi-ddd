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
