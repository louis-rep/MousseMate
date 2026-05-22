from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserRead, UserSearchResult
from app.services import follow as follow_service
from app.services import user as user_service

router = APIRouter()


@router.get("/users/search", response_model=tuple[UserSearchResult, ...])
def search_users(
    q: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[UserSearchResult, ...]:
    if not q.strip():
        return ()
    return follow_service.search_users(db, query=q.strip(), current_user_id=current_user.id)


@router.get("/mates", response_model=tuple[UserRead, ...])
def list_mates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[UserRead, ...]:
    return tuple(follow_service.list_following(db, user_id=current_user.id))


@router.post("/follow/{user_id}", status_code=status.HTTP_201_CREATED)
def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")
    target = user_service.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    if follow_service.follow_user(db, follower_id=current_user.id, followed_id=user_id) is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Already following user {user_id}")


@router.delete("/unfollow/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not follow_service.unfollow_user(db, follower_id=current_user.id, followed_id=user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Not following user {user_id}")
