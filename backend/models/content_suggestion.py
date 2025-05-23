from sqlalchemy import (
    Column, String, Integer, ForeignKey, DateTime, Text, JSON, Float,
    ARRAY, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class ContentSuggestion(Base):
    __tablename__ = "content_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"))
    section = Column(String)
    original_text = Column(Text)
    suggested_text = Column(Text)
    confidence_score = Column(Float)
    ai_model = Column(String)
    created_at = Column(DateTime, default=now)

    page = relationship("Page", back_populates="suggestions")