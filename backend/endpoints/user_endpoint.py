from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from controller.user.register import register_user
from schemas.user import UserCreate
from db.session import get_session 

router = APIRouter()

@router.post("/register")
def register_user_route(request: UserCreate, db: Session = Depends(get_session)):
    try:
        user = register_user(db, request)
        return {"message": "User registered", "user_id": str(user.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User registration failed: {e}")
