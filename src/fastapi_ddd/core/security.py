from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from fastapi import Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_ddd.core.config import settings
from fastapi_ddd.core.database import get_session

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password=password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(password=plain_password, hash=hashed_password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", refreshUrl="/api/auth/refresh")


def _create_token(
    data: dict, token_type: str, expires_delta: timedelta | None = None
) -> str:
    """Generic function to create JWT tokens"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiry times based on token type
        default_expiry = (
            timedelta(minutes=15) if token_type == "access" else timedelta(days=7)
        )
        expire = datetime.now(timezone.utc) + default_expiry

    to_encode.update(
        {"exp": expire, "iat": datetime.now(timezone.utc), "type": token_type}
    )

    encoded_jwt = jwt.encode(
        payload=to_encode, key=settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT Access token"""
    return _create_token(data, token_type="access", expires_delta=expires_delta)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT Refresh token"""
    return _create_token(data, token_type="refresh", expires_delta=expires_delta)


def _decode_token(token: str, expected_type: str) -> dict:
    """Generic function to decode and validate JWT tokens"""
    try:
        payload = jwt.decode(
            jwt=token, key=settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{expected_type.capitalize()} token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_access_token(token: str) -> dict:
    """Decode and validate access token"""
    return _decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> dict:
    """Decode and validate refresh token"""
    return _decode_token(token, expected_type="refresh")
