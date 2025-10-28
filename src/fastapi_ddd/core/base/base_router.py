from typing import Type
from fastapi import APIRouter, Depends, Query
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
    exclude_routes: list[str] | None = None,
    permissions: dict[str, list] | None = None,
) -> APIRouter:
    """
    Generate a complete CRUD router.

    Args:
        service_factory: Callable that takes session and returns service
        create_schema: Pydantic schema for POST
        read_schema: Pydantic schema for responses
        update_schema: Pydantic schema for PUT
        prefix: URL Prefix
        tags: OpenAPI tags
        exclude_routes: List of routes to exclude. Options: ['create', 'read_list', 'read_one', 'update', 'delete']

    Returns:
        APIRouter with CRUD endpoints (excluding any specified)

    Usage:
        router = create_crud_router(
            service_factory=get_user_service,
            create_schema=UserCreateSchema,
            read_schema=UserReadSchema,
            update_schema=UserUpdateSchema,
            prefix="/users",
            tags=["users"],
            exclude_routes=["delete"]  # Don't allow deletion
        )
    """
    if exclude_routes is None:
        exclude_routes = []

    router = APIRouter(prefix=prefix, tags=tags)

    # CREATE
    if "create" not in exclude_routes:

        @router.post(
            "/",
            response_model=read_schema,
            status_code=201,
            dependencies=permissions.get("create", []),
        )
        async def create(
            obj_in: create_schema, session: AsyncSession = Depends(get_session)
        ):
            service = service_factory(session)
            return await service.create(obj_in)

    # READ LIST
    if "read_list" not in exclude_routes:

        @router.get(
            "/",
            response_model=Page[read_schema],
            dependencies=permissions.get("read_list", []),
        )
        async def get_list(
            session: AsyncSession = Depends(get_session),
            search: str | None = Query(
                None,
                description="Search term to match against searchable fields",
                min_length=1,
            ),
            order_by: str | None = Query(
                None,
                description="Field name to sort by (e.g., 'created_at', 'username')",
            ),
            order: str = Query(
                "asc",
                description="Sort order: 'asc' for ascending or 'desc' for descending",
            ),
        ):
            """Get paginated list of records.

            Supports:
            - Search across configured fields
            - Dynamic ordering via query parameters
            - Pagination (page, size)
            """
            service = service_factory(session)

            # Build order_by expression if provided
            order_expr = None
            if order_by:
                model = service.repository.model
                column = getattr(model, order_by, None)
                if column is not None:
                    order_expr = column.desc() if order == "desc" else column

            return await service.get_multi_paginated(order_by=order_expr, search=search)

    # READ SINGLE
    if "read_one" not in exclude_routes:

        @router.get(
            "/{id}",
            response_model=read_schema,
            dependencies=permissions.get("read_one", []),
        )
        async def get_one(id: int, session: AsyncSession = Depends(get_session)):
            service = service_factory(session)
            return await service.get(id)

    # UPDATE
    if "update" not in exclude_routes:

        @router.put(
            "/{id}",
            response_model=read_schema,
            dependencies=permissions.get("update", []),
        )
        async def update(
            id: int, obj_in: update_schema, session: AsyncSession = Depends(get_session)
        ):
            service = service_factory(session)
            return await service.update(id, obj_in)

    # DELETE
    if "delete" not in exclude_routes:

        @router.delete(
            "/{id}",
            status_code=204,
            dependencies=permissions.get("delete", []),
        )
        async def delete(id: int, session: AsyncSession = Depends(get_session)):
            """Delete a record"""
            service = service_factory(session)
            await service.delete(id)

    return router
