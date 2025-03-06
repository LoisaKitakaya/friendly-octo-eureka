import requests
from users.models import User
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.template.loader import render_to_string

TEMPLATE_CODE_NAME_MAP = {
    "PR": "temps/password_reset.html",
    "WE": "temps/manager_welcome_email.html",
    "AV": "temps/account_verification.html",
    "PC": "temps/payment_confirmation.html",
    "GN": "temps/general_notification.html",
}


def find_template(template_code_name: str) -> str:
    try:
        template = TEMPLATE_CODE_NAME_MAP.get(template_code_name)

        if not template:
            raise Exception(f"Unknown template code: {template_code_name}.")

        return template
    except Exception as e:
        raise Exception(str(e))


@shared_task
def send_email(
    subject: str,
    receiver_email_address: str,
    sender_email_address: str = settings.EMAIL_HOST_USER,
    **kwargs,
):
    mail_data = kwargs.get("mail_data", None)

    template_code_name = kwargs.get("template_code_name", None)

    if template_code_name and mail_data:
        template = find_template(str(template_code_name))

        html_content = render_to_string(template_name=template, context=dict(mail_data))

        plain_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=plain_content,
            from_email=sender_email_address,
            recipient_list=[
                receiver_email_address,
            ],
            html_message=html_content,
            fail_silently=False,
        )

    send_mail(
        subject=subject,
        message=str(kwargs.get("message")),
        from_email=sender_email_address,
        recipient_list=[
            receiver_email_address,
        ],
        fail_silently=False,
    )


@shared_task
def create_notification(recipient_id: str, message: str, url_path: str):
    try:
        payload = {
            "recipient_id": recipient_id,
            "message": message,
            "url_path": url_path,
        }

        base_url = settings.TALKS_URL

        url = f"{base_url}/notifications/webhook"

        try:
            res = requests.post(url, json=payload, timeout=5)

            if res.status_code != 200 or res.json().get("status") != "success":
                raise Exception(
                    f"Failed to create notification. Status code: {res.status_code}."
                )

            return True
        except Exception as e:
            raise Exception(str(e))
    except Exception as e:
        raise Exception(str(e))
