from datetime import datetime, timedelta, timezone
from jose import jwt
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY, ALGORITHM

def create_access_token(subject: str, expires_delta: int = None) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=expires_delta or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"exp": expires, "sub": subject}
    return jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)

def create_refresh_token(subject: str, expires_delta: int = None) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=expires_delta or REFRESH_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"exp": expires, "sub": subject}
    return jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
