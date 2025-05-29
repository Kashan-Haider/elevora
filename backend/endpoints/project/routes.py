from fastapi import APIRouter, Depends, Header, HTTPException, Query
from models import User, Project, Page, AuditDetail
from schemas.project import ProjectCreate, ProjectOut
from sqlalchemy.orm import Session
from db.session import get_session
from jose import JWTError
from uuid import uuid4
from utils.user.getUserByToken import getUserByToken
from typing import List
from pydantic import BaseModel, Field
from utils.audit.audit_site import auditSite


router = APIRouter()
class SiteAuditRequest(BaseModel):
    project_id:str = Field(...)
    url: str = Field(...)
    max_urls_per_domain: int = 3
    max_pages: int = 2


@router.post("/create-project", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    authorization: str = Header(...),
    session: Session = Depends(get_session)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    user = getUserByToken(token, session)
    try:
        if not user.id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")

    # Step 2: Check if user exists
    user = session.query(User).filter(User.id == user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Step 3: Create and store the project
    new_project = Project(
        id=uuid4(),
        user_id=user.id,
        name=payload.name,
        domain=payload.domain
    )
    session.add(new_project)
    session.commit()
    session.refresh(new_project)

    return new_project


@router.get('/get-all-projects', response_model=List[ProjectOut])
def get_projects(user_id: str = Query(...), session: Session = Depends(get_session)):
    projects = session.query(Project).filter(Project.user_id == user_id).all()
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found for this user.")
    return projects

    
    
    



@router.post("/audit")
async def audit_site(request: SiteAuditRequest, session:Session = Depends(get_session), authorization: str = Header(...),):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    user = getUserByToken(token, session)
    try:
        audit = auditSite(
            session= session,
            project_id = request.project_id,
            url=request.url,
            depth=request.max_urls_per_domain,
            max_pages=request.max_pages,
        )
        return {"message": audit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Site audit failed: {e}")
    
    
    
    
# @router.get('/get-audit-data')
# async def get_audit_data(project_id: str, session: Session = Depends(get_session)):
#     # Check if project exists and get audit details in a single query
#     audit_details = session.query(AuditDetail)\
#         .join(Page, AuditDetail.page_id == Page.id)\
#         .join(Project, Page.project_id == Project.id)\
#         .filter(Project.id == project_id)\
#         .all()
    
#     # If no audit details found, check if project exists
#     if not audit_details:
#         project_exists = session.query(Project).filter(Project.id == project_id).first()
#         if not project_exists:
#             raise HTTPException(status_code=404, detail="Project not found")
#         # Project exists but no audit details yet - return empty list
#         return []
    
#     return audit_details


@router.get("/get-audit-data")
async def get_audit_data(project_id: str, session: Session = Depends(get_session)):
    project = session.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Gather all pages for this project
    pages = session.query(Page).filter(Page.project_id == project_id).all()
    if not pages:
        return {"project": {"id": project_id, "name": project.name}, "pages": []}

    result = []

    for page in pages:
        # Get all audit details for this page
        audits = session.query(AuditDetail).filter(AuditDetail.page_id == page.id).order_by(
            AuditDetail.category, AuditDetail.subcategory
        ).all()
        
        # Organize audit data by categories
        audit_data = {
            "summary": {},
            "metadata": {},
            "content": {},
            "technical": {},
            "links": {},
            "media": {},
            "international": {},
            "performance": {},
            "accessibility": {},
            "issues": [],
            "recommendations": [],
            "all_details": []
        }
        
        # Counters for summary
        critical_count = 0
        warning_count = 0
        pass_count = 0
        total_recommendations = 0
        
        for audit in audits:
            # Build comprehensive audit detail object
            audit_detail = {
                "id": str(audit.id),
                "category": audit.category,
                "subcategory": audit.subcategory,
                "metric_name": audit.metric_name,
                "metric_value": audit.metric_value,
                "text_value": audit.text_value,
                "boolean_value": audit.boolean_value,
                "json_value": audit.json_value,
                "status": audit.status,
                "severity": audit.severity,
                "score": audit.score,
                "max_score": audit.max_score,
                "recommendations": audit.recommendations or [],
                "details": audit.details,
                "message": audit.message,
                "created_at": audit.created_at.isoformat() if audit.created_at else None
            }
            
            # Add to all_details
            audit_data["all_details"].append(audit_detail)
            
            # Categorize by audit category
            if audit.category in audit_data:
                if audit.subcategory not in audit_data[audit.category]:
                    audit_data[audit.category][audit.subcategory] = []
                audit_data[audit.category][audit.subcategory].append(audit_detail)
            
            # Count status types for summary
            if audit.status in ['fail', 'critical']:
                critical_count += 1
            elif audit.status in ['warning', 'needs_improvement']:
                warning_count += 1
            elif audit.status in ['pass', 'good', 'excellent']:
                pass_count += 1
                
            # Collect issues
            if audit.status in ['fail', 'critical', 'warning', 'needs_improvement']:
                audit_data["issues"].append({
                    "category": audit.category,
                    "subcategory": audit.subcategory,
                    "message": audit.message,
                    "status": audit.status,
                    "severity": audit.severity,
                    "recommendations": audit.recommendations or []
                })
            
            # Collect all recommendations
            if audit.recommendations:
                total_recommendations += len(audit.recommendations)
                for rec in audit.recommendations:
                    audit_data["recommendations"].append({
                        "category": audit.category,
                        "subcategory": audit.subcategory,
                        "recommendation": rec,
                        "priority": audit.severity or "low"
                    })
        
        # Build summary data
        total_audits = len(audits)
        audit_data["summary"] = {
            "total_checks": total_audits,
            "critical_issues": critical_count,
            "warnings": warning_count,
            "passed": pass_count,
            "total_recommendations": total_recommendations,
            "overall_score": page.audit_score or 0,
            "seo_score": page.seo_score or 0,
            "health_status": (
                "critical" if critical_count > 5 else
                "needs_attention" if critical_count > 2 or warning_count > 5 else
                "good" if warning_count <= 2 else "excellent"
            )
        }
        
        # Build comprehensive page data
        page_data = {
            "page_info": {
                "id": str(page.id),
                "url": page.url,
                "title": page.title,
                "meta_description": page.meta_description,
                "last_audited": page.last_audited.isoformat() if page.last_audited else None,
                "word_count": page.word_count,
                "page_size_bytes": page.page_size_bytes,
                "total_links": page.total_links,
                "total_images": page.total_images,
                "issues_count": page.issues_count or 0,
                "opportunities_count": page.opportunities_count or 0
            },
            "scores": {
                "overall": page.audit_score or 0,
                "seo": page.seo_score or 0
            },
            "content_analysis": {
                "word_count": page.word_count or 0,
                "text_html_ratio": page.text_html_ratio or 0,
                "paragraphs_count": page.paragraphs_count or 0,
                "headings": {
                    "h1": page.h1_count or 0,
                    "h2": page.h2_count or 0,
                    "h3": page.h3_count or 0,
                    "h4": page.h4_count or 0,
                    "h5": page.h5_count or 0,
                    "h6": page.h6_count or 0,
                    "data": page.headings_data
                }
            },
            "links_analysis": {
                "total": page.total_links or 0,
                "internal": page.internal_links_count or 0,
                "external": page.external_links_count or 0,
                "internal_with_text_percentage": page.internal_links_with_text_percentage or 0,
                "external_with_nofollow_percentage": page.external_links_with_nofollow_percentage or 0
            },
            "images_analysis": {
                "total": page.total_images or 0,
                "with_alt": page.images_with_alt or 0,
                "without_alt": page.images_without_alt or 0,
                "alt_percentage": page.images_with_alt_percentage or 0
            },
            "technical_seo": {
                "has_https": page.has_https or False,
                "has_viewport_meta": page.has_viewport_meta or False,
                "has_mobile_friendly": page.has_mobile_friendly_design or False,
                "has_favicon": page.has_favicon or False,
                "has_doctype": page.has_doctype or False,
                "has_structured_data": page.has_structured_data or False,
                "structured_data_count": page.structured_data_count or 0,
                "canonical_matches_url": page.canonical_matches_url or False
            },
            "audit_details": audit_data
        }
        
        result.append(page_data)

    # Sort pages by last_audited (most recent first)
    result.sort(key=lambda x: x["page_info"]["last_audited"] or "", reverse=True)

    return {
        "project": {
            "id": project_id,
            "name": project.name,
            "total_pages": len(result)
        },
        "pages": result
    }

