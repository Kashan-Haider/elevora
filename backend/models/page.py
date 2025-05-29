from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base, default_uuid, now

class Page(Base):
    __tablename__ = "pages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    content_hash = Column(String, nullable=True)
    page_size_bytes = Column(Integer, nullable=True)
    
    # SEO Scores
    last_audited = Column(DateTime, nullable=True)
    audit_score = Column(Float, nullable=True)  # Overall audit score
    performance_score = Column(Float, nullable=True)
    seo_score = Column(Float, nullable=True)
    accessibility_score = Column(Float, nullable=True)
    
    # Content Analysis
    word_count = Column(Integer, nullable=True)
    text_html_ratio = Column(Float, nullable=True)
    paragraphs_count = Column(Integer, nullable=True)
    
    # Meta Information
    title_length = Column(Integer, nullable=True)
    meta_description_length = Column(Integer, nullable=True)
    meta_robots = Column(String, nullable=True)
    meta_keywords = Column(Text, nullable=True)
    meta_viewport = Column(String, nullable=True)
    meta_charset = Column(String, nullable=True)
    canonical_url = Column(String, nullable=True)
    canonical_matches_url = Column(Boolean, nullable=True)
    language = Column(String, nullable=True)
    has_language = Column(Boolean, default=False)
    
    # Technical SEO
    has_https = Column(Boolean, default=False)
    has_viewport_meta = Column(Boolean, default=False)
    has_mobile_friendly_design = Column(Boolean, default=False)
    has_favicon = Column(Boolean, default=False)
    favicon_url = Column(String, nullable=True)
    has_doctype = Column(Boolean, default=False)
    
    # Structured Data
    has_structured_data = Column(Boolean, default=False)
    structured_data_count = Column(Integer, default=0)
    structured_data_types = Column(JSON, nullable=True)
    structured_data = Column(JSON, nullable=True)
    
    # Social Media Tags
    meta_og_tags = Column(JSON, nullable=True)
    meta_twitter_tags = Column(JSON, nullable=True)
    
    # Headings Analysis
    headings_data = Column(JSON, nullable=True)  # All heading content and structure
    h1_count = Column(Integer, default=0)
    h2_count = Column(Integer, default=0)
    h3_count = Column(Integer, default=0)
    h4_count = Column(Integer, default=0)
    h5_count = Column(Integer, default=0)
    h6_count = Column(Integer, default=0)
    
    # Links Analysis
    total_links = Column(Integer, default=0)
    internal_links_count = Column(Integer, default=0)
    external_links_count = Column(Integer, default=0)
    internal_links_with_text = Column(Integer, default=0)
    external_links_with_text = Column(Integer, default=0)
    internal_links_with_text_percentage = Column(Float, default=0)
    external_links_with_nofollow = Column(Integer, default=0)
    external_links_with_nofollow_percentage = Column(Float, default=0)
    internal_links_data = Column(JSON, nullable=True)  # Detailed internal links
    external_links_data = Column(JSON, nullable=True)  # Detailed external links
    
    # Images Analysis
    total_images = Column(Integer, default=0)
    images_with_alt = Column(Integer, default=0)
    images_without_alt = Column(Integer, default=0)
    images_with_alt_percentage = Column(Float, default=0)
    images_data = Column(JSON, nullable=True)  # Detailed image analysis
    
    # Media Content
    videos_count = Column(Integer, default=0)
    audios_count = Column(Integer, default=0)
    videos_data = Column(JSON, nullable=True)
    audios_data = Column(JSON, nullable=True)
    
    # Content Enhancement
    strong_tags_count = Column(Integer, default=0)
    em_tags_count = Column(Integer, default=0)
    b_tags_count = Column(Integer, default=0)
    i_tags_count = Column(Integer, default=0)
    strong_tags_data = Column(JSON, nullable=True)
    em_tags_data = Column(JSON, nullable=True)
    b_tags_data = Column(JSON, nullable=True)
    i_tags_data = Column(JSON, nullable=True)
    
    # Keywords and Content
    keywords_density = Column(JSON, nullable=True)
    paragraphs_data = Column(JSON, nullable=True)  # Store paragraph content for analysis
    
    # Technical Resources
    script_sources_count = Column(Integer, default=0)
    style_links_count = Column(Integer, default=0)
    inline_styles = Column(Integer, default=0)
    inline_scripts = Column(Integer, default=0)
    script_sources = Column(JSON, nullable=True)
    style_links = Column(JSON, nullable=True)
    
    # Resource Hints
    resource_hints = Column(JSON, nullable=True)
    
    # International SEO
    has_hreflang = Column(Boolean, default=False)
    hreflang_tags = Column(JSON, nullable=True)
    
    # Counters for quick access
    issues_count = Column(Integer, default=0)
    opportunities_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=now)
    
    # Relationships
    project = relationship("Project", back_populates="pages")
    audit_details = relationship("AuditDetail", back_populates="page", cascade="all, delete-orphan")
    content_suggestions = relationship("ContentSuggestion", back_populates="page", cascade="all, delete-orphan")