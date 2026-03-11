# core/tasks.py
from huey.contrib.djhuey import task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@task()
def send_async_email(subject, message, recipient_list, from_email=None):
    """
    Фоновая задача для отправки Email. 
    Пользователь не ждет ответа от SMTP сервера.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f"Email sent to {recipient_list}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
        # Можно добавить логику повтора (retry) при ошибке