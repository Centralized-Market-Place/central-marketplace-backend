from dataclasses import dataclass
import logging
import traceback
from datetime import datetime, UTC, timedelta
from typing import Optional

from centeral_marketplace.admin_invites.repository import AdminInvitationRepository
from centeral_marketplace.channels.repository import ChannelRepository
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.notifications.core import NotificationType
from centeral_marketplace.notifications.service import NotificationService
from centeral_marketplace.products.repository import ProductRepository
from centeral_marketplace.reports.core import (
    AdminDashboardStats,
    InviteStatistics,
    Report,
    ReportCreate,
    ReportReview,
    ReportStatistics,
    ReportStatus,
    ReportTarget,
    ReportType,
    SellerApplicationStatistics,
    UserStatistics,
)
from centeral_marketplace.reports.repository import ReportRepository
from centeral_marketplace.sellers.repository import SellerApplicationRepository
from centeral_marketplace.users.core import Role, User
from centeral_marketplace.users.repository import UserRepository
from fastapi import HTTPException, status
from injector import inject, singleton

from core import PyObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


@singleton
@inject
@dataclass
class ReportService:
    report_repository: ReportRepository
    user_repository: UserRepository
    product_repository: ProductRepository
    channel_repository: ChannelRepository
    notification_service: NotificationService
    seller_repository: SellerApplicationRepository
    admin_invite_repository: AdminInvitationRepository

    def create_report(self, reporter: User, report_data: ReportCreate) -> Report:
        try:
            try:
                self.report_repository.find_existing_report(
                    reporter.id, report_data.target_id, report_data.target_type.value
                )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already reported this item",
                )

            target_title = self._validate_and_get_target_title(
                report_data.target_id, report_data.target_type
            )

            now = datetime.now(UTC)
            report = Report(
                reporter_id=reporter.id,
                target_id=report_data.target_id,
                target_type=report_data.target_type,
                report_type=report_data.report_type,
                message=report_data.message,
                status=ReportStatus.PENDING,
                created_at=now,
                reporter_name=f"{reporter.first_name} {reporter.last_name or ''}".strip(),
                target_title=target_title,
            )

            saved_report = self.report_repository.save(report)
            self._notify_admins_new_report(saved_report)

            logger.info(f"Report created: {saved_report.id} by user {reporter.id}")
            return saved_report

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating report: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create report",
            ) from e

    def get_all_reports(
        self,
        pagination: Pagination = None,
        status_filter: Optional[ReportStatus] = None,
        target_type_filter: Optional[ReportTarget] = None,
        report_type_filter: Optional[ReportType] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> PaginatedResponse[Report]:
        try:
            criteria = {}
            if status_filter:
                criteria["status"] = status_filter.value
            if target_type_filter:
                criteria["target_type"] = target_type_filter.value
            if report_type_filter:
                criteria["report_type"] = report_type_filter.value

            return self.report_repository.find_all_by_dict(
                criteria=criteria,
                pagination=pagination,
                sort_by=sort_by,
                sort_desc=sort_desc,
            )
        except Exception as e:
            logger.error(f"Error getting reports: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve reports",
            ) from e

    def get_user_reports(
        self, user_id: PyObjectId, pagination: Pagination = None
    ) -> PaginatedResponse[Report]:
        try:
            criteria = {"reporter_id": user_id}
            return self.report_repository.find_all_by_dict(
                criteria=criteria,
                pagination=pagination,
                sort_by="created_at",
                sort_desc=True,
            )
        except Exception as e:
            logger.error(f"Error getting user reports: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve user reports",
            ) from e

    def get_report(self, report_id: PyObjectId) -> Report:
        try:
            report = self.report_repository.find_one(report_id)
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Report not found",
                )
            return report
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting report {report_id}: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve report",
            ) from e

    def review_report(
        self, admin: User, report_id: PyObjectId, review_data: ReportReview
    ) -> Report:
        try:
            report = self.get_report(report_id)

            if report.status != ReportStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Report has already been reviewed",
                )

            now = datetime.now(UTC)
            report.status = review_data.status
            report.reviewed_by = admin.id
            report.reviewed_at = now
            report.admin_notes = review_data.admin_notes
            if review_data.status == ReportStatus.APPROVED:
                self._handle_report_approval(report)

            updated_report = self.report_repository.save(report)

            self._notify_reporter_decision(updated_report, admin)

            logger.info(
                f"Report {report.id} reviewed by admin {admin.id} with status {review_data.status}"
            )
            return updated_report

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error reviewing report: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to review report",
            ) from e

    def _validate_and_get_target_title(
        self, target_id: PyObjectId, target_type: ReportTarget
    ) -> str:
        if target_type == ReportTarget.PRODUCT:
            product = self.product_repository.find_one(target_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found",
                )
            return product.title or "Untitled Product"
        elif target_type == ReportTarget.CHANNEL:
            channel = self.channel_repository.find_one(target_id)
            if not channel:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Channel not found",
                )
            return channel.title or channel.username or "Unnamed Channel"

    def _handle_report_approval(self, report: Report):
        try:
            if report.target_type == ReportTarget.PRODUCT:
                product = self.product_repository.find_one_product(report.target_id)
                if product:
                    product.is_deleted = True
                    self.product_repository.save(product)
                    logger.info(
                        f"Product {report.target_id} marked as deleted due to approved report"
                    )

            elif report.target_type == ReportTarget.CHANNEL:
                channel = self.channel_repository.find_one(report.target_id)
                if channel:
                    channel.is_suspended = True
                    self.channel_repository.save(channel)
                    logger.info(
                        f"Channel {report.target_id} suspended due to approved report"
                    )

        except Exception:
            logger.error(f"Error handling report approval: {traceback.format_exc()}")

    def _notify_admins_new_report(self, report: Report):
        try:
            admin_criteria = {
                "role": {"$in": [Role.ADMIN.value, Role.SUPER_ADMIN.value]}
            }
            admin_users = self.user_repository.find_all_by_dict(admin_criteria)

            message = (
                f"New report submitted for {report.target_type.lower()}: {report.target_title}. "
                f"Report type: {report.report_type.replace('_', ' ').title()}. "
                f"Reporter: {report.reporter_name}"
            )

            for admin in admin_users.items:
                self.notification_service.create_notification(
                    user_id=admin.id,
                    content=message,
                    notification_type=NotificationType.SYSTEM,
                )

        except Exception:
            logger.error(
                f"Error notifying admins about new report: {traceback.format_exc()}"
            )

    def _notify_reporter_decision(self, report: Report, admin: User):
        try:
            if report.status == ReportStatus.APPROVED:
                message = (
                    f"Your report about {report.target_type.lower()} '{report.target_title}' "
                    f"has been approved. Thank you for helping keep our platform safe."
                )
            else:
                message = (
                    f"Your report about {report.target_type.lower()} '{report.target_title}' "
                    f"has been reviewed and rejected. "
                    f"{report.admin_notes or 'No additional notes provided.'}"
                )

            self.notification_service.create_notification(
                user_id=report.reporter_id,
                content=message,
                notification_type=NotificationType.SYSTEM,
            )

        except Exception:
            logger.error(
                f"Error notifying reporter about decision: {traceback.format_exc()}"
            )

    def get_report_statistics(self) -> ReportStatistics:
        try:
            total_reports = self.report_repository.count_all_by_dict({})
            pending_reports = self.report_repository.count_all_by_dict(
                {"status": ReportStatus.PENDING.value}
            )
            approved_reports = self.report_repository.count_all_by_dict(
                {"status": ReportStatus.APPROVED.value}
            )
            rejected_reports = self.report_repository.count_all_by_dict(
                {"status": ReportStatus.REJECTED.value}
            )

            return ReportStatistics(
                total_reports=total_reports,
                pending_reports=pending_reports,
                approved_reports=approved_reports,
                rejected_reports=rejected_reports,
            )
        except Exception as e:
            logger.error(f"Error getting report statistics: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve report statistics",
            ) from e

    def get_seller_application_statistics(self) -> SellerApplicationStatistics:
        try:
            total_applications = self.seller_repository.count_all_by_dict({})
            pending_applications = self.seller_repository.count_all_by_dict(
                {"status": "PENDING"}
            )
            approved_applications = self.seller_repository.count_all_by_dict(
                {"status": "APPROVED"}
            )
            rejected_applications = self.seller_repository.count_all_by_dict(
                {"status": "REJECTED"}
            )

            return SellerApplicationStatistics(
                total_applications=total_applications,
                pending_applications=pending_applications,
                approved_applications=approved_applications,
                rejected_applications=rejected_applications,
            )
        except Exception as e:
            logger.error(
                f"Error getting seller application statistics: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve seller application statistics",
            ) from e

    def get_user_statistics(self) -> UserStatistics:
        try:
            total_users = self.user_repository.count_all_by_dict({})

            active_users = self.user_repository.count_all_by_dict(
                {"is_deleted": {"$ne": True}}
            )

            admin_users = self.user_repository.count_all_by_dict(
                {"role": {"$in": [Role.ADMIN.value, Role.SUPER_ADMIN.value]}}
            )
            seller_users = self.user_repository.count_all_by_dict(
                {"role": Role.SELLER.value}
            )

            thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
            new_users_last_30_days = self.user_repository.count_all_by_dict(
                {"created_at": {"$gte": thirty_days_ago}}
            )

            return UserStatistics(
                total_users=total_users,
                active_users=active_users,
                admin_users=admin_users,
                seller_users=seller_users,
                new_users_last_30_days=new_users_last_30_days,
            )
        except Exception as e:
            logger.error(f"Error getting user statistics: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve user statistics",
            ) from e

    def get_invite_statistics(self) -> InviteStatistics:
        try:
            total_invites = self.admin_invite_repository.count_all_by_dict({})
            pending_invites = self.admin_invite_repository.count_all_by_dict(
                {"status": "PENDING"}
            )
            accepted_invites = self.admin_invite_repository.count_all_by_dict(
                {"status": "ACCEPTED"}
            )

            now = datetime.now(UTC)
            expired_invites = self.admin_invite_repository.count_all_by_dict(
                {"expires_at": {"$lt": now}, "status": "PENDING"}
            )

            return InviteStatistics(
                total_invites=total_invites,
                pending_invites=pending_invites,
                accepted_invites=accepted_invites,
                expired_invites=expired_invites,
            )
        except Exception as e:
            logger.error(f"Error getting invite statistics: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve invite statistics",
            ) from e

    def get_dashboard_statistics(self, current_user: User) -> AdminDashboardStats:
        try:
            reports = self.get_report_statistics()
            seller_applications = self.get_seller_application_statistics()
            users = self.get_user_statistics()
            invites = self.get_invite_statistics()

            return AdminDashboardStats(
                reports=reports,
                seller_applications=seller_applications,
                users=users,
                invites=invites,
            )
        except Exception as e:
            logger.error(
                f"Error getting dashboard statistics: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve dashboard statistics",
            ) from e
