from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class AuditDetail(Base):
    """Stores detailed metrics from SEO audits for data visualization"""
    __tablename__ = "audit_details"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    audit_run_id = Column(String, nullable=False)  # To group results from same audit run
    category = Column(String, nullable=False)  # metadata, content, media, technical, links, international
    subcategory = Column(String, nullable=False)  # title, meta_description, headings, etc.
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=True)
    text_value = Column(Text, nullable=True)
    boolean_value = Column(Boolean, nullable=True)
    json_value = Column(JSON, nullable=True)
    severity = Column(String, nullable=True)  # critical, high, medium, low, info
    status = Column(String, nullable=True)  # pass, fail, warning, info, excellent, good, needs_improvement
    message = Column(Text, nullable=True)  # Human readable message/suggestion
    recommendations = Column(JSON, nullable=True)  # Array of recommendation strings
    details = Column(JSON, nullable=True)  # Additional structured details
    score = Column(Float, nullable=True)  # Individual metric score
    max_score = Column(Float, nullable=True)  # Maximum possible score for this metric
    created_at = Column(DateTime, default=now)
    
    # Relationships
    page = relationship("Page", back_populates="audit_details")