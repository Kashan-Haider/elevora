from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from models import User
from jose import jwt
from config import JWT_SECRET_KEY, ALGORITHM
from db.session import get_session

def getUserByToken(token: str, session: Session) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Invalid token: no subject")

        user = session.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return user
    except Exception as e:
        raise HTTPException(
            status_code=403, detail=f"Token is invalid or expired: {str(e)}"
        )