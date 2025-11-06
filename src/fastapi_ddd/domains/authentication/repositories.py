from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_ddd.core.base.base_repository import BaseRepository
from .models import User


class UserRepository(BaseRepository[User]):
    """
    User specific repository with custom queries.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        """Find user by username"""
        q = select(User).where(User.username == username)
        result = await self.session.exec(q)
        return result.one_or_none()

    async def check_unique(
        self, username: str, email: str, exclude_id: int | None = None
    ) -> tuple[bool, str | None]:
        """
        Check if username/email are unique
        Returns:
            (is_unique, error_msg)
        """
        q = select(User).where(or_(User.username == username, User.email == email))
        if exclude_id:
            q = q.where(User.id != exclude_id)

        result = await self.session.exec(q)
        existing = result.one_or_none()

        if existing:
            if existing.username == username:
                return False, "Username exists"
            if existing.email == email:
                return False, "Email exists"

        return True, None

    async def get_by_username_or_email(self, identifier: str) -> User | None:
        """Find user by username or email"""
        q = select(User).where(
            or_(User.username == identifier, User.email == identifier)
        )

        result = await self.session.exec(q)
        return result.one_or_none()
