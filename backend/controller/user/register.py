from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate 
from uuid import uuid4
from datetime import datetime


def register_user(db: Session, user_data: UserCreate) -> User:
    new_user = User(
        id=uuid4(),
        email=user_data.email,
        password_hash=user_data.password,  # Ideally hash this
        created_at=datetime.utcnow()
    )
    print(new_user)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
