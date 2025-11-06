from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_ddd.core.security import oauth2_scheme, decode_access_token
from fastapi_ddd.core.database import get_session
from .models import User
from .repositories import UserRepository


async def _get_user_from_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
    strict: bool = True,
) -> User:
    """
    Internal function to get user from JWT token.
    """
    payload = decode_access_token(token)

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(session=session)
    user = await repo.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if strict and user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Dependency to get current authenticated user (strict mode - excludes deleted users).
    Use this in protected endpoints: current_user: Annotated[User, Depends(get_current_user)]
    """
    return await _get_user_from_token(token=token, session=session, strict=True)


async def get_current_user_non_strict(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Dependency to get current user (non-strict mode - includes deleted users).
    """
    return await _get_user_from_token(token=token, session=session, strict=False)
