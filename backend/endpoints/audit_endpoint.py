# from fastapi import APIRouter, HTTPException, BackgroundTasks
# from pydantic import BaseModel, Field
# import json
# from datetime import datetime
# import os
# from controller.audit.audit_site import audit as auditSite

# router = APIRouter()


# class SiteAuditRequest(BaseModel):
#     url: str = Field(...)
#     max_urls_per_domain: int = 3
#     max_pages: int = 2


# @router.post("/audit")
# async def audit_site(request: SiteAuditRequest):
#     try:
#         audit = auditSite(
#             url=request.url,
#             depth=request.max_urls_per_domain,
#             max_pages=request.max_pages,
#         )
#         return {"message": audit}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Site audit failed: {e}")