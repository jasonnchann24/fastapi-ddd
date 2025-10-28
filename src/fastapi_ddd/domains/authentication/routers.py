from fastapi import APIRouter
from sqlalchemy import select
from fastapi_ddd.core.database import SessionDep
from .schemas import UserCreateSchema, UserReadSchema
from .models import User
from fastapi import HTTPException
from fastapi_pagination.ext.sqlalchemy import apaginate
from fastapi_pagination import Page

router = APIRouter(prefix="/auth", tags=["authentication"])

responses_409_conflict = {
    400: {
        "description": "Username or email already exists",
        "content": {
            "application/json": {
                "example": {"detail": "Username or email already exists"}
            }
        },
    },
}


@router.post("/users", response_model=UserReadSchema, responses=responses_409_conflict)
@router.post(
    "/register", response_model=UserReadSchema, responses=responses_409_conflict
)
async def create_user(user: UserCreateSchema, session: SessionDep) -> User:
    exist_email_or_username = await session.exec(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )
    if exist_email_or_username.first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    db_user = User.model_validate(user)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.get("/users", response_model=Page[UserReadSchema])
async def get_users(
    session: SessionDep,
) -> Page[UserReadSchema]:
    return await apaginate(session, select(User).order_by(User.created_at.desc()))


@router.get("/users/{user_id}", response_model=UserReadSchema)
async def get_user(user_id: int, session: SessionDep) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserReadSchema)
async def update_user(
    user_id: int, user_update: UserCreateSchema, session: SessionDep
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check for username or email conflicts
    exist_email_or_username = await session.exec(
        select(User).where(
            (
                (User.username == user_update.username)
                | (User.email == user_update.email)
            )
            & (User.id != user_id)
        )
    )
    if exist_email_or_username.first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user.username = user_update.username
    user.email = user_update.email
    user.password_hash = user_update.password

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(user_id: int, session: SessionDep) -> dict:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()
    return {"detail": "User deleted successfully"}
