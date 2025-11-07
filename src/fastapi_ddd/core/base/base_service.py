from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from fastapi import HTTPException, status
from fastapi_pagination import Page
from uuid import UUID

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic service for business logics.

    Usage:
        class UserService(BaseService[User, UserCreateSchema, UserUpdateSchema]):
            def __init__(self, repository: UserRepository):
                super().__init__(repository)
    """

    def __init__(self, repository):
        self.repository = repository

    def get_default_order_by(self):
        """Override in subclass to set default ordering"""
        return self.repository.model.id.desc()

    def get_searchable_fields(self) -> list[str]:
        """
        Override in subclass to define which fields are searchable.

        Example:
            def get_searchable_fields(self):
                return ['username', 'email', 'first_name', 'last_name']
        """
        return []

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create new record"""
        obj_in = await self.before_create(obj_in) or obj_in
        obj_dict = obj_in.model_dump()
        obj = await self.repository.create(obj_dict)
        await self.after_create(obj)
        return obj

    async def get(self, id: UUID) -> ModelType:
        """Get a record by ID, raise 404 if not found"""
        db_obj = await self.repository.get(id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                default=f"Record with id {id} not found.",
            )
        return db_obj

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100, order_by=None
    ) -> list[ModelType]:
        """Get multiple records"""
        if order_by is None:
            order_by = self.get_default_order_by()
        return await self.repository.get_multi(
            skip=skip, limit=limit, order_by=order_by
        )

    async def get_multi_paginated(
        self, *, order_by=None, search: str | None = None
    ) -> Page[ModelType]:
        """
        Get paginated records with optional search.

        Args:
            order_by: Column expression for ordering
            search: Search term to match against searchable fields
        """
        if order_by is None:
            order_by = self.get_default_order_by()

        # Build search parameters if search provided
        search_fields = None
        search_value = None
        if search and self.get_searchable_fields():
            search_fields = self.get_searchable_fields()
            search_value = search

        return await self.repository.get_multi_paginated(
            order_by=order_by, search_fields=search_fields, search_value=search_value
        )

    async def update(self, id: UUID, obj_in: UpdateSchemaType) -> ModelType:
        """Update a record, raise 404 if not found"""
        obj_in = await self.before_update(id, obj_in) or obj_in

        await self.get(id)

        obj_dict = obj_in.model_dump(exclude_unset=True)
        db_obj = await self.repository.update(id, obj_dict)
        await self.after_update(db_obj)
        return db_obj

    async def force_delete(self, id: UUID) -> bool:
        """Force delete a record"""
        await self.before_delete(id)
        success = await self.repository.force_delete(id)
        await self.after_delete(id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record with id {id} not found.",
            )
        return True

    async def delete(self, id: UUID) -> bool:
        """Soft delete a record"""
        await self.before_delete(id)

        if hasattr(self.repository.model, "deleted_at"):
            success = await self.repository.soft_delete(id)
        else:
            success = await self.repository.force_delete(id)
        await self.after_delete(id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record with id {id} not found.",
            )
        return True

    async def before_create(
        self, obj_in: CreateSchemaType
    ) -> Optional[CreateSchemaType]:
        return obj_in

    async def after_create(self, obj: ModelType) -> None:
        pass

    async def before_update(
        self, obj_id: UUID, obj_in: UpdateSchemaType
    ) -> Optional[UpdateSchemaType]:
        return obj_in

    async def after_update(self, obj: ModelType) -> None:
        pass

    async def before_delete(self, obj_id: UUID) -> None:
        pass

    async def after_delete(self, obj_id: UUID) -> None:
        pass
