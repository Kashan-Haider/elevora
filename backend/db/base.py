from sqlalchemy.orm import declarative_base
import uuid
import datetime

Base = declarative_base()

def default_uuid():
    return str(uuid.uuid4())

def now():
    return datetime.datetime.utcnow()
