from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from controller.user.register import register_user
from schemas.user import UserCreate, UserResponse
from db.session import get_session
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user_route(request: UserCreate, db: Session = Depends(get_session)):
    try:
        user = register_user(db, request)
        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )