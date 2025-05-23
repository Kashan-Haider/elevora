from sqlalchemy import (
    Column, Integer, ForeignKey, DateTime, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    competitor_url = Column(Text, nullable=False)
    keywords = Column(JSON)
    backlinks = Column(Integer)
    domain_authority = Column(Integer)
    created_at = Column(DateTime, default=now)

    project = relationship("Project", back_populates="competitors")