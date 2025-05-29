from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(Text, nullable=False)
    search_intent = Column(String, nullable=True)
    volume = Column(Integer, nullable=True)
    difficulty = Column(Integer, nullable=True)
    relevance_score = Column(Float, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=now)

    # Relationships
    project = relationship("Project", back_populates="keywords")
