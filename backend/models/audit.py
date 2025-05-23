from sqlalchemy import (
    Column, String, ForeignKey, DateTime, Integer, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class Audit(Base):
    __tablename__ = "audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"))
    audit_type = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    issues = Column(JSON)
    recommendations = Column(JSON)
    created_at = Column(DateTime, default=now)

    page = relationship("Page", back_populates="audits")