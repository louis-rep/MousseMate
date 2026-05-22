from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead
from app.services import user as user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    if user_service.get_by_username(db, data.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    return user_service.create_user(db, data)


@router.post("/login", response_model=Token)
def login(data: UserCreate, db: Session = Depends(get_db)) -> Token:
    user = user_service.get_by_username(db, data.username)
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
