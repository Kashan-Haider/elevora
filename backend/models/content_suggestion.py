from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class ContentSuggestion(Base):
    __tablename__ = "content_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    section = Column(String, nullable=True)
    original_text = Column(Text, nullable=True)
    suggested_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    ai_model = Column(String, nullable=True)
    created_at = Column(DateTime, default=now)

    page = relationship("Page", back_populates="content_suggestions")