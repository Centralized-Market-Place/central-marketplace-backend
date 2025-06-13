import os
import base64
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sib_api_v3_sdk import (
    Configuration,
    ApiClient,
    TransactionalEmailsApi,
    SendSmtpEmail,
)
from sib_api_v3_sdk.rest import ApiException
from config import Config
from injector import inject, singleton
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union
from fastapi import BackgroundTasks

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


@inject
@singleton
@dataclass
class EmailService:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.config = Config()

    def render_template(self, template_name: str, **context):
        if "current_year" not in context:
            context["current_year"] = datetime.now().strftime("%Y")

        template = self.env.get_template(template_name)
        return template.render(**context)

    def _get_logo_content(self, use_dark_theme: bool = False) -> Optional[str]:
        logo_file = "dark_theme_logo.jpg" if use_dark_theme else "light_theme_logo.jpg"
        logo_path = os.path.join(ASSETS_DIR, logo_file)

        try:
            with open(logo_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        except Exception as e:
            print(f"ERROR: Failed to process logo file {logo_path}: {str(e)}")
            return None

    def send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        text_content: str,
        html_content: str = None,
        from_email: str = None,
        use_dark_theme: bool = False,
    ) -> Dict[str, Any]:
        if not self.config.brevo_api_key:
            raise ValueError("BREVO_API_KEY is not set in environment variables")

        configuration = Configuration()
        configuration.api_key["api-key"] = self.config.brevo_api_key

        api_client = ApiClient(configuration)
        api_instance = TransactionalEmailsApi(api_client)

        recipients = to_email if isinstance(to_email, list) else [to_email]
        to_list = [{"email": email} for email in recipients]

        sender_email = from_email or self.config.email_from

        logo_content = self._get_logo_content(use_dark_theme)

        email_params = {
            "sender": {"name": "Central Marketplace", "email": sender_email},
            "to": to_list,
            "subject": subject,
            "text_content": text_content,
            "html_content": html_content,
        }

        if logo_content:
            logo_file = (
                "dark_theme_logo.jpg" if use_dark_theme else "light_theme_logo.jpg"
            )
            email_params["attachment"] = []
            email_params["attachment"].append(
                {
                    "content": logo_content,
                    "name": logo_file,
                    "type": "image/jpeg",
                    "disposition": "inline",
                    "id": "logo",
                }
            )

        send_smtp_email = SendSmtpEmail(**email_params)

        try:
            api_response = api_instance.send_transac_email(send_smtp_email)
            return {
                "status": "success",
                "message": "Email sent",
                "response": api_response,
            }
        except ApiException as e:
            error_msg = f"Error sending email: {e}"
            return {"status": "error", "message": error_msg}

    def send_email_background(
        self,
        background_tasks: BackgroundTasks,
        to_email: Union[str, List[str]],
        subject: str,
        text_content: str,
        html_content: str = None,
        from_email: str = None,
        use_dark_theme: bool = False,
    ):
        background_tasks.add_task(
            self.send_email,
            to_email=to_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            from_email=from_email,
            use_dark_theme=use_dark_theme,
        )

    def send_verification_email(
        self,
        to_email: str,
        verification_link: str,
        user_name: str = "",
        from_email: str = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ):
        subject = "Verify your email address"
        text_content = f"Hello {user_name}, please verify your email using the following link: {verification_link}"
        html_content = self.render_template(
            "verification_email.html",
            user_name=user_name,
            verification_link=verification_link,
        )

        if background_tasks:
            return self.send_email_background(
                background_tasks=background_tasks,
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
            )
        else:
            return self.send_email(
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
            )

    def send_password_reset_email(
        self,
        to_email: str,
        reset_link: str,
        user_name: str = "",
        from_email: str = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ):
        subject = "Reset your password"
        text_content = f"Hello {user_name}, reset your password using the following link: {reset_link}"
        html_content = self.render_template(
            "password_reset_email.html", user_name=user_name, reset_link=reset_link
        )

        if background_tasks:
            return self.send_email_background(
                background_tasks=background_tasks,
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
            )
        else:
            return self.send_email(
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
            )

    def send_notification_email(
        self,
        to_email: str,
        message: str,
        user_name: str = "",
        from_email: str = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ):
        subject = "Notification from Central Marketplace"
        text_content = f"Hello {user_name}, {message}"
        html_content = self.render_template(
            "notification_email.html", user_name=user_name, message=message
        )

        if background_tasks:
            return self.send_email_background(
                background_tasks=background_tasks,
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
            )
        else:
            return self.send_email(
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
            )

    def send_admin_invitation_email(
        self,
        to_email: str,
        invitation_link: str,
        role: str,
        invited_by_name: str,
        expires_at,
        from_email: str = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ):
        subject = "Admin Invitation - Central Marketplace"
        text_content = f"You have been invited to join Central Marketplace as an {role} by {invited_by_name}. Click the following link to accept: {invitation_link}"
        html_content = self.render_template(
            "admin_invitation_email.html",
            invitation_link=invitation_link,
            role=role,
            invited_by_name=invited_by_name,
            expires_at=expires_at,
        )

        if background_tasks:
            return self.send_email_background(
                background_tasks=background_tasks,
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
            )
        else:
            return self.send_email(
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
            )
