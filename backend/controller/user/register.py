from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate
from uuid import uuid4
from datetime import datetime
from passlib.hash import bcrypt

def register_user(db: Session, user_data: UserCreate) -> User:
    # Hash the password before storing
    hashed_password = bcrypt.hash(user_data.password)
    
    new_user = User(
        id=uuid4(),
        email=user_data.email,
        password_hash=hashed_password,
        created_at=datetime.utcnow()
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise e