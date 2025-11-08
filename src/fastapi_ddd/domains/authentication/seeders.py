from sqlmodel.ext.asyncio.session import AsyncSession
from .repositories import UserRepository
from .models import User
from .schemas import UserCreateSchema


class FakeUserSeeder:
    DEFAULT_USERS = [
        UserCreateSchema(
            username="superadmin",
            email="superadmin@test.com",
            full_name="Super admin",
            password="123123123",
        ),
        UserCreateSchema(
            username="admin",
            email="admin@test.com",
            full_name="Admin",
            password="123123123",
        ),
        UserCreateSchema(
            username="reguser",
            email="reguser@test.com",
            full_name="Reg user",
            password="123123123",
        ),
    ]

    def __init__(self, users: list[UserCreateSchema] | None = None):
        self.users = users or self.DEFAULT_USERS

    async def seed(self, session: AsyncSession) -> list[User]:
        repo = UserRepository(session=session)
        created = []
        for u in self.users:
            new_user = await repo.create(u.model_dump())
            created.append(new_user)

        return created
