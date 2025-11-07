from typing import Generic, TypeVar, Type, Any
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_
from fastapi_pagination.ext.sqlalchemy import apaginate
from fastapi_pagination import Page
from uuid import UUID

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for CRUD operations.
    Usage:
        user_repo = BaseRepository(session, User)
        user = await user_repo.get(user_id)
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get(self, id: UUID) -> ModelType | None:
        """Get single record by ID"""
        return await self.session.get(self.model, id)

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100, order_by: Any = None
    ) -> list[ModelType]:
        """Get multiple records with pagination"""
        query = select(self.model).offset(skip).limit(limit)

        if order_by is not None:
            query = query.order_by(order_by)

        result = await self.session.exec(query)
        return result.all()

    async def get_multi_paginated(
        self,
        *,
        order_by: Any = None,
        filters: dict[str, Any] | None = None,
        search_fields: list[str] | None = None,
        search_value: str | None = None,
    ) -> Page[ModelType]:
        """
        Get records with automatic pagination, filtering, and search.

        Args:
            order_by: Column expression for ordering
            filters: Dict of field_name: value for exact match filtering
            search_fields: List of field names to search in (ILIKE)
            search_value: Value to search for (uses LIKE/ILIKE across search_fields)

        Uses fastapi-pagination for page/size parameters.

        Example:
            # Exact filtering
            await repo.get_multi_paginated(filters={'status': 'active'})

            # Search
            await repo.get_multi_paginated(
                search_fields=['username', 'email'],
                search_value='john'
            )

            # Combined
            await repo.get_multi_paginated(
                filters={'status': 'active'},
                search_fields=['username'],
                search_value='admin',
                order_by=User.created_at.desc()
            )
        """
        query = select(self.model)

        # Apply exact match filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)

        # Apply search (ILIKE across multiple fields)
        if search_value and search_fields:
            conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    column = getattr(self.model, field)
                    conditions.append(column.ilike(f"%{search_value}%"))

            if conditions:
                query = query.where(or_(*conditions))

        if order_by is not None:
            query = query.order_by(order_by)

        return await apaginate(self.session, query)

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """
        Create a new record.

        NOTE: Does NOT commit. Caller must:
        - Call session.commit() for simple operations
        - Use transaction() wrapper for complex operations
        """
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, id: UUID, obj_in: dict[str, Any]) -> ModelType | None:
        """Update record. Does not commit"""
        db_obj = await self.get(id)
        if not db_obj:
            return None

        for field, value in obj_in.items():
            # Only set fields that exist on the model
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def force_delete(self, id: UUID) -> bool:
        """Delete permanently record. Does not commit"""
        db_obj = await self.get(id)
        if not db_obj:
            return False

        await self.session.delete(db_obj)
        await self.session.flush()
        return True

    async def soft_delete(self, id: UUID) -> bool:
        """Soft delete a record. Does not commit"""
        db_obj = await self.get(id)
        if not db_obj:
            return False

        from datetime import datetime

        db_obj.deleted_at = datetime.now()
        self.session.add(db_obj)
        await self.session.flush()
        return True

    async def exists(self, **filters) -> bool:
        """
        Check if record exists with given filters.

        Usage:
            await repo.exists(username="john")
            await repo.exists(email="test@example.com")
        """
        query = select(self.model)
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.session.exec(query)
        return result.first() is not None

    async def get_by(self, **filters) -> ModelType | None:
        """
        Get single record by filters.

        Usage:
            await repo.get_by(username="john")
            await repo.get_by(resource="users", action="create")
        """
        query = select(self.model)
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.session.exec(query)
        return result.first()

    async def exists_excluding(self, exclude_id: Any, **filters) -> bool:
        """
        Check if record exists with given filters, excluding a specific ID.
        Useful for uniqueness validation during updates.

        Usage:
            # Check if username exists for other users
            await repo.exists_excluding(user_id, username="john")

            # Check if role name exists for other roles
            await repo.exists_excluding(role_id, name="admin")
        """
        query = select(self.model).where(self.model.id != exclude_id)
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.session.exec(query)
        return result.first() is not None
