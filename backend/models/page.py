from sqlalchemy import (
    Column, String, ForeignKey, DateTime, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class Page(Base):
    __tablename__ = "pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    url = Column(Text, nullable=False)
    title = Column(Text)
    status = Column(String, default="active")
    last_audited = Column(DateTime)
    created_at = Column(DateTime, default=now)

    project = relationship("Project", back_populates="pages")
    audits = relationship("Audit", back_populates="page", cascade="all, delete")
    suggestions = relationship("ContentSuggestion", back_populates="page", cascade="all, delete")