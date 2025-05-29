from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from jose import jwt
from models.model import User
from database.db import get_session
from config import JWT_SECRET_KEY, ALGORITHM

def get_current_username(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=403, detail="Invalid username")
        return username
    except:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

def get_current_user(token: str = Header(...), session: Session = Depends(get_session)) -> User:
    token = token.replace("Bearer ", "")
    username = get_current_username(token)
    user = session.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
