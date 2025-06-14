from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from fastapi_injector import Injected

from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.reports.core import (
    Report,
    ReportCreate,
    ReportReview,
    ReportStatus,
    ReportTarget,
    ReportType,
)
from centeral_marketplace.reports.service import ReportService
from centeral_marketplace.users.core import Role, User
from middleware import get_current_user, require_role
from core import PyObjectId


reports_router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


@reports_router.post("/", response_model=Report, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: ReportService = Injected(ReportService),
):
    return report_service.create_report(current_user, report_data)


@reports_router.get("/", response_model=PaginatedResponse[Report])
async def get_all_reports(
    _: Annotated[User, Depends(require_role([Role.ADMIN.value, Role.SUPER_ADMIN.value]))],
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[ReportStatus] = Query(None, description="Filter by report status"),
    target_type_filter: Optional[ReportTarget] = Query(None, description="Filter by target type"),
    report_type_filter: Optional[ReportType] = Query(None, description="Filter by report type"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    report_service: ReportService = Injected(ReportService),
):
    pagination = Pagination(page=page, size=page_size)
    return report_service.get_all_reports(
        pagination=pagination,
        status_filter=status_filter,
        target_type_filter=target_type_filter,
        report_type_filter=report_type_filter,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


@reports_router.get("/me", response_model=PaginatedResponse[Report])
async def get_my_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = 1,
    page_size: int = 10,
    report_service: ReportService = Injected(ReportService),
):
    pagination = Pagination(page=page, size=page_size)
    return report_service.get_user_reports(current_user.id, pagination)


@reports_router.get("/{report_id}", response_model=Report)
async def get_report(
    report_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: ReportService = Injected(ReportService),
):
    report = report_service.get_report(report_id)
    
    if (
        current_user.role not in [Role.ADMIN, Role.SUPER_ADMIN]
        and str(report.reporter_id) != str(current_user.id)
    ):
      
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this report",
        )
    
    return report


@reports_router.post("/{report_id}/review", response_model=Report)
async def review_report(
    report_id: PyObjectId,
    review_data: ReportReview,
    current_user: Annotated[User, Depends(require_role([Role.ADMIN.value, Role.SUPER_ADMIN.value]))],
    report_service: ReportService = Injected(ReportService),
):
    return report_service.review_report(current_user, report_id, review_data) 