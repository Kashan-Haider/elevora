# audit_service.py
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from models.page import Page
from models.audit_detail import AuditDetail, AuditIssue, SeoOpportunity

class AuditStorageService:
    """Service for storing comprehensive audit results in the database"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def store_audit_results(self, page_id: str, audit_data: Dict[str, Any]) -> str:
        """
        Store comprehensive audit results in the database
        Returns the audit_run_id for tracking
        """
        audit_run_id = str(uuid.uuid4())
        
        try:
            # Update page with audit summary
            self._update_page_summary(page_id, audit_data, audit_run_id)
            
            # Store detailed metrics
            self._store_audit_details(page_id, audit_run_id, audit_data)
            
            # Store issues
            self._store_audit_issues(page_id, audit_run_id, audit_data)
            
            # Store opportunities
            self._store_seo_opportunities(page_id, audit_run_id, audit_data)
            
            self.db.commit()
            return audit_run_id
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def _update_page_summary(self, page_id: str, audit_data: Dict[str, Any], audit_run_id: str):
        """Update page with summary information"""
        page = self.db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise ValueError(f"Page with id {page_id} not found")
        
        # Update basic page info
        page.last_audited = datetime.now()
        
        # Extract and store page metadata
        if 'metadata' in audit_data:
            metadata = audit_data['metadata']
            page.title = metadata.get('title', page.title)
            page.meta_description = metadata.get('meta_description', page.meta_description)
        
        # Store scores if available
        if 'scores' in audit_data:
            scores = audit_data['scores']
            page.audit_score = scores.get('overall', 0)
            page.performance_score = scores.get('performance', 0)
            page.seo_score = scores.get('seo', 0)
            page.accessibility_score = scores.get('accessibility', 0)
        
        # Count issues and opportunities
        page.issues_count = len(audit_data.get('issues', []))
        page.opportunities_count = len(audit_data.get('opportunities', []))
    
    def _store_audit_details(self, page_id: str, audit_run_id: str, audit_data: Dict[str, Any]):
        """Store detailed audit metrics"""
        details_to_store = [
            # Metadata details
            ('metadata', 'title', audit_data.get('metadata', {}).get('title')),
            ('metadata', 'meta_description', audit_data.get('metadata', {}).get('meta_description')),
            ('metadata', 'h1_count', audit_data.get('metadata', {}).get('h1_count')),
            ('metadata', 'h2_count', audit_data.get('metadata', {}).get('h2_count')),
            ('metadata', 'word_count', audit_data.get('metadata', {}).get('word_count')),
            
            # Technical details
            ('technical', 'page_size', audit_data.get('technical', {}).get('page_size')),
            ('technical', 'load_time', audit_data.get('technical', {}).get('load_time')),
            ('technical', 'mobile_friendly', audit_data.get('technical', {}).get('mobile_friendly')),
            ('technical', 'ssl_enabled', audit_data.get('technical', {}).get('ssl_enabled')),
            
            # Content details
            ('content', 'images_count', audit_data.get('content', {}).get('images_count')),
            ('content', 'images_without_alt', audit_data.get('content', {}).get('images_without_alt')),
            ('content', 'internal_links', audit_data.get('content', {}).get('internal_links')),
            ('content', 'external_links', audit_data.get('content', {}).get('external_links')),
            
            # Performance metrics
            ('performance', 'first_contentful_paint', audit_data.get('performance', {}).get('fcp')),
            ('performance', 'largest_contentful_paint', audit_data.get('performance', {}).get('lcp')),
            ('performance', 'cumulative_layout_shift', audit_data.get('performance', {}).get('cls')),
        ]
        
        for category, subcategory, value in details_to_store:
            if value is not None:
                detail = AuditDetail(
                    page_id=page_id,
                    audit_run_id=audit_run_id,
                    category=category,
                    subcategory=subcategory,
                    metric_name=subcategory,
                    **self._get_value_column(value)
                )
                self.db.add(detail)
        
        # Store structured data if available
        if 'structured_data' in audit_data:
            detail = AuditDetail(
                page_id=page_id,
                audit_run_id=audit_run_id,
                category='technical',
                subcategory='structured_data',
                metric_name='schema_markup',
                json_value=audit_data['structured_data']
            )
            self.db.add(detail)
    
    def _store_audit_issues(self, page_id: str, audit_run_id: str, audit_data: Dict[str, Any]):
        """Store audit issues"""
        issues = audit_data.get('issues', [])
        
        for issue_data in issues:
            issue = AuditIssue(
                page_id=page_id,
                audit_run_id=audit_run_id,
                issue_type=issue_data.get('type', 'general'),
                title=issue_data.get('title', 'Unknown Issue'),
                description=issue_data.get('description'),
                severity=issue_data.get('severity', 'medium'),
                element=issue_data.get('element'),
                recommendation=issue_data.get('recommendation'),
                how_to_fix=issue_data.get('how_to_fix'),
                impact_score=issue_data.get('impact_score')
            )
            self.db.add(issue)
    
    def _store_seo_opportunities(self, page_id: str, audit_run_id: str, audit_data: Dict[str, Any]):
        """Store SEO opportunities"""
        opportunities = audit_data.get('opportunities', [])
        
        for opp_data in opportunities:
            opportunity = SeoOpportunity(
                page_id=page_id,
                audit_run_id=audit_run_id,
                opportunity_type=opp_data.get('type', 'general'),
                title=opp_data.get('title', 'SEO Opportunity'),
                description=opp_data.get('description'),
                priority=opp_data.get('priority', 'medium'),
                estimated_impact=opp_data.get('estimated_impact'),
                effort_required=opp_data.get('effort_required'),
                action_items=opp_data.get('action_items'),
                metrics=opp_data.get('metrics')
            )
            self.db.add(opportunity)
    
    def _get_value_column(self, value: Any) -> Dict[str, Any]:
        """Determine which column to store the value in based on its type"""
        if isinstance(value, bool):
            return {'boolean_value': value}
        elif isinstance(value, (int, float)):
            return {'metric_value': float(value)}
        elif isinstance(value, str):
            return {'text_value': value}
        elif isinstance(value, (dict, list)):
            return {'json_value': value}
        else:
            return {'text_value': str(value)}
    
    def get_latest_audit_results(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the latest audit results for a page"""
        # Get the latest audit run
        latest_detail = (
            self.db.query(AuditDetail)
            .filter(AuditDetail.page_id == page_id)
            .order_by(AuditDetail.created_at.desc())
            .first()
        )
        
        if not latest_detail:
            return None
        
        audit_run_id = latest_detail.audit_run_id
        
        # Get all details for this audit run
        details = (
            self.db.query(AuditDetail)
            .filter(AuditDetail.page_id == page_id, AuditDetail.audit_run_id == audit_run_id)
            .all()
        )
        
        # Get issues for this audit run
        issues = (
            self.db.query(AuditIssue)
            .filter(AuditIssue.page_id == page_id, AuditIssue.audit_run_id == audit_run_id)
            .all()
        )
        
        # Get opportunities for this audit run
        opportunities = (
            self.db.query(SeoOpportunity)
            .filter(SeoOpportunity.page_id == page_id, SeoOpportunity.audit_run_id == audit_run_id)
            .all()
        )
        
        return {
            'audit_run_id': audit_run_id,
            'details': [self._detail_to_dict(d) for d in details],
            'issues': [self._issue_to_dict(i) for i in issues],
            'opportunities': [self._opportunity_to_dict(o) for o in opportunities]
        }
    
    def _detail_to_dict(self, detail: AuditDetail) -> Dict[str, Any]:
        return {
            'category': detail.category,
            'subcategory': detail.subcategory,
            'metric_name': detail.metric_name,
            'value': detail.metric_value or detail.text_value or detail.boolean_value or detail.json_value,
            'created_at': detail.created_at.isoformat()
        }
    
    def _issue_to_dict(self, issue: AuditIssue) -> Dict[str, Any]:
        return {
            'type': issue.issue_type,
            'title': issue.title,
            'description': issue.description,
            'severity': issue.severity,
            'element': issue.element,
            'recommendation': issue.recommendation,
            'how_to_fix': issue.how_to_fix,
            'impact_score': issue.impact_score
        }
    
    def _opportunity_to_dict(self, opportunity: SeoOpportunity) -> Dict[str, Any]:
        return {
            'type': opportunity.opportunity_type,
            'title': opportunity.title,
            'description': opportunity.description,
            'priority': opportunity.priority,
            'estimated_impact': opportunity.estimated_impact,
            'effort_required': opportunity.effort_required,
            'action_items': opportunity.action_items,
            'metrics': opportunity.metrics
        }