from fastapi import APIRouter, Depends, Header, HTTPException
from models import User, Project
from schemas.user import UserCreate, UserLogin
from sqlalchemy.orm import Session
from utils.auth.hashing import hash_password, verify_password
from utils.auth.jwt_handler import create_access_token, create_refresh_token
from db.session import get_session
from jose import jwt
from config import JWT_SECRET_KEY, ALGORITHM, JWT_REFRESH_SECRET_KEY
from pydantic import BaseModel
from utils.user.getUserByToken import getUserByToken


router = APIRouter()

@router.post("/signup")
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    existing_email = session.query(User).filter(User.email == user.email).first()
    existing_username = session.query(User).filter(User.username == user.username).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    elif existing_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(
        username = user.username, email=user.email, password_hash=hash_password(user.password)
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "User registered successfully"}

@router.post("/login")
def login_user(user: UserLogin, session: Session = Depends(get_session)):
    registered_user = session.query(User).filter(User.username == user.username).first()
    if not registered_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(user.password, registered_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {
        "access_token": create_access_token(subject=user.username),
        "refresh_token": create_refresh_token(subject=user.username),
    }
    

@router.post("/current-user")
def read_user(
    session: Session = Depends(get_session),
    Authorization: str = Header(None),
):

    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = Authorization.replace("Bearer ", "")
    try:
        user = getUserByToken(token, session=session)
        return {
            "user": user
        }

    except Exception as e:
        raise HTTPException(
            status_code=403, detail=f"Token is invalid or expired: {str(e)}"
        )


@router.get("/verify-token/{token}")
def verify_user_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, ALGORITHM)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="username is not valid")
        return payload
    except:
        raise HTTPException(status_code=403, detail="Token is invalid or expired")


class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
    
@router.post("/refresh")
def refresh_access_token(request: RefreshTokenRequest):
    try:
        payload = jwt.decode(request.refresh_token, JWT_REFRESH_SECRET_KEY, ALGORITHM)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Invalid refresh token")
        return {"access_token": create_access_token(subject=username)}
    except:
        raise HTTPException(status_code=403, detail="Invalid or expired refresh token")

@router.post("/has-project", )
def has_user_project(
    session: Session = Depends(get_session),
    Authorization: str = Header(None)
):
    

    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = Authorization.replace("Bearer ", "")
    try:
        user = getUserByToken(token, session=session)
        count = session.query(Project).filter(Project.user_id == user.id).count()
        return count>0
    except Exception as e:
        raise HTTPException(
            status_code=403, detail=f"Token is invalid or expired: {str(e)}"
        )
        
        




