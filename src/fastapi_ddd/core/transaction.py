"""
Database transaction management utilities.

Provides explicit transaction control when needed:
- Use for multi-step operations that must be atomic
- Use for operations that need rollback on partial failure
- Don't use for simple reads or single writes (overhead)
"""

from contextlib import asynccontextmanager
from functools import wraps
from typing import Callable, TypeVar, Any, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


@asynccontextmanager
async def transaction(session: AsyncSession):
    """
    Explicit transaction context manager.

    Use when you need atomic multi-step operations:
    - Creating related records (user + profile + logs)
    - Transferring data (debit one account, credit another)
    - Bulk operations that must succeed/fail together

    Auto-commits on success, auto-rolls back on exception.

    Usage:
        async with transaction(session):
            await user_repo.create(user_data)
            await profile_repo.create(profile_data)
            # Both commit together or rollback together

    Args:
        session: SQLAlchemy async session

    Raises:
        Exception: Re-raises any exception after rollback
    """
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e


def transactional(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """
    Decorator for automatic transaction management.

    Use for service methods that always need transactions.

    Usage:
        @transactional
        async def create_user_with_profile(session: AsyncSession, user_data, profile_data):
            user = await user_repo.create(user_data)
            await profile_repo.create({...})
            return user

    Args:
        func: Async function to wrap with transaction

    Returns:
        Wrapped function with transaction management
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = kwargs.get("session")

        if not session:
            for arg in args:
                if isinstance(arg, AsyncSession):
                    session = arg
                    break

        if not session:
            raise ValueError(
                f"@transactional decorator requires an AsyncSession parameter. "
                f"Function '{func.__name__}' doesn't have 'session' parameter."
            )

        try:
            result = await func(*args, **kwargs)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            raise e

    return wrapper


class DB:
    """
    Provides explicit transaction control:
    - DB.transaction
    - DB.commit
    - DB.rollback
    """

    @staticmethod
    async def transaction(
        session: AsyncSession, callback: Callable[[AsyncSession], Awaitable[T]]
    ) -> T:
        """
        Execute callback within a transaction.
        Usage:
            result = await DB.transaction(session, async lambda s: (
                    await user_repo.create(data)
                ))
        """
        try:
            result = await callback(session)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            raise e

    @staticmethod
    async def commit(session: AsyncSession) -> None:
        """Manually commit the current transaction."""
        await session.commit()

    @staticmethod
    async def rollback(session: AsyncSession) -> None:
        """Manually rollback the current transaction."""
        await session.rollback()

    @staticmethod
    @asynccontextmanager
    async def nested_transaction(session: AsyncSession):
        """
        Begin a nested transaction (savepoint).

        Usage:
            async with transaction(session):
                await operation1()

                async with DB.nested_transaction(session):
                    await risky_operation()  # Can rollback just this

                await operation2()
        """
        async with session.begin_nested():
            yield session


__all__ = ["transaction", "transactional", "DB"]
