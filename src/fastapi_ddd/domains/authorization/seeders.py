from sqlmodel.ext.asyncio.session import AsyncSession
from .repositories import RoleRepository
from .models import Role
from .schemas import RoleCreateSchema, RoleReadSchema
from uuid import UUID


class RoleSeeder:
    """
    Idempotent seeder for roles
    """

    DEFAULT_ROLES = [
        RoleCreateSchema(name="superadmin", description="Full system access"),
        RoleCreateSchema(name="admin", description="Admin system access"),
        RoleCreateSchema(name="user", description="Regular user system access"),
    ]

    def __init__(self, roles: list[RoleCreateSchema] | None = None):
        self.roles = roles or self.DEFAULT_ROLES

    async def seed(self, session: AsyncSession) -> list[Role]:
        repo = RoleRepository(session=session)
        created_or_found = []

        desired_names = {r.name for r in self.roles}
        existing = await repo.get_by_names(desired_names)
        existing_map = {role.name: role for role in existing}

        for r in self.roles:
            if r.name in existing_map:
                created_or_found.append(existing_map[r.name])
                continue

            new_role = RoleCreateSchema(
                name=r.name, description=r.description, is_active=r.is_active
            )
            created = await repo.create(new_role.model_dump())
            created_or_found.append(created)

        return created_or_found
