from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    created_at = Column(DateTime, default=now)

    # Relationships with cascade delete
    user = relationship("User", back_populates="projects")
    pages = relationship("Page", back_populates="project", cascade="all, delete-orphan", lazy="joined")
    keywords = relationship("Keyword", back_populates="project", cascade="all, delete-orphan", lazy="joined")
    competitors = relationship("Competitor", back_populates="project", cascade="all, delete-orphan", lazy="joined")