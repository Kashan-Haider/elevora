from sqlalchemy import (
    Column, String, Integer, ForeignKey, DateTime, Text, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    keyword = Column(Text, nullable=False)
    search_intent = Column(String)
    volume = Column(Integer)
    difficulty = Column(Integer)
    relevance_score = Column(Float)
    source = Column(String)
    created_at = Column(DateTime, default=now)

    project = relationship("Project", back_populates="keywords")