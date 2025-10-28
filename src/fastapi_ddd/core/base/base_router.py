from typing import Type
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_pagination import Page

from fastapi_ddd.core.database import get_session


def create_crud_router(
    *,
    service_factory,
    create_schema: Type[BaseModel],
    read_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    prefix: str,
    tags: list[str],
) -> APIRouter:
    """
    Generate a complete CRUD router.

    Args:
        service_factory: Callable that takes session and returns service
        create_schema: Pydantic
        read_schema: Pydantic
        update_schema: Pydantic
        prefix: URL Prefix
        tags: OpenAPI tags
        resource_name: Name for resource

    Returns:
        APIRouter with 5 endpoints

    Usage:
        def get_user_service(session: AsyncSession):
            return UserService(UserRepository(session))

        router = create_crud_router(
            service_factory=get_user_service,
            create_schema=UserCreateSchema,
            read_schema=UserReadSchema,
            update_schema=UserUpdateSchema,
            prefix="/users,
            tags=["users"],
            resource_name="User"
        )
    """

    router = APIRouter(prefix=prefix, tags=tags)

    @router.post("/", response_model=read_schema, status_code=201)
    async def create(
        obj_in: create_schema, session: AsyncSession = Depends(get_session)
    ):
        service = service_factory(session)
        return await service.create(obj_in)

    @router.get("/", response_model=Page[read_schema])
    async def get_list(
        session: AsyncSession = Depends(get_session),
        order_by: str | None = None,
        order: str = "asc",
    ):
        """Get paginated list.

        Query parameters:
        - order_by: Field name to order by (e.g., 'created_at')
        - order: 'asc' for ascending or 'desc' for descending (default: 'asc')
        """
        service = service_factory(session)

        # Build order_by expression if provided
        order_expr = None
        if order_by:
            model = service.repository.model
            column = getattr(model, order_by, None)
            if column is not None:
                order_expr = column.desc() if order == "desc" else column

        return await service.get_multi_paginated(order_by=order_expr)

    @router.get("/{id}", response_model=read_schema)
    async def get_one(id: int, session: AsyncSession = Depends(get_session)):
        service = service_factory(session)
        return await service.get(id)

    @router.put("/{id}", response_model=read_schema)
    async def update(
        id: int, obj_in: update_schema, session: AsyncSession = Depends(get_session)
    ):
        service = service_factory(session)
        return await service.update(id, obj_in)

    @router.delete("/{id}", status_code=204)
    async def delete(id: int, session: AsyncSession = Depends(get_session)):
        """Delete a record"""
        service = service_factory(session)
        await service.delete(id)

    return router
