from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    competitor_url = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=True)
    backlinks = Column(Integer, nullable=True)
    domain_authority = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=now)

    # Relationships
    project = relationship("Project", back_populates="competitors")
