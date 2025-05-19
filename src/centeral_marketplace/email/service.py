import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException
from config import settings

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_template(template_name: str, **context):
    template = env.get_template(template_name)
    return template.render(**context)

def send_email(to_email: str, subject: str, text_content: str, html_content: str = None):
    if not settings.brevo_api_key:
        raise ValueError("BREVO_API_KEY is not set in environment variables")

    
    configuration = Configuration()
    configuration.api_key['api-key'] = settings.brevo_api_key

    
    api_client = ApiClient(configuration)
    api_instance = TransactionalEmailsApi(api_client)

    
    send_smtp_email = SendSmtpEmail(
        sender={"name": "Your Name", "email": settings.email_from},
        to=[{"email": to_email}],
        subject=subject,
        text_content=text_content,
        html_content=html_content
    )

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email sent successfully: {api_response}")
        return {"status": "success", "message": "Email sent"}
    except ApiException as e:
        print(f"Error sending email: {e}")
        return {"status": "error", "message": str(e)}

def send_verification_email(to_email: str, verification_link: str, user_name: str = ""):
    subject = "Verify your email address"
    text_content = f"Hello {user_name}, please verify your email using the following link: {verification_link}"
    html_content = render_template('verification_email.html', user_name=user_name, verification_link=verification_link)
    return send_email(to_email, subject, text_content, html_content)

def send_password_reset_email(to_email: str, reset_link: str, user_name: str = ""):
    subject = "Reset your password"
    text_content = f"Hello {user_name}, reset your password using the following link: {reset_link}"
    html_content = render_template('password_reset_email.html', user_name=user_name, reset_link=reset_link)
    return send_email(to_email, subject, text_content, html_content)

def send_notification_email(to_email: str, message: str, user_name: str = ""):
    subject = "Notification from Central Marketplace"
    text_content = f"Hello {user_name}, {message}"
    html_content = render_template('notification_email.html', user_name=user_name, message=message)
    return send_email(to_email, subject, text_content, html_content)