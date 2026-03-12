# core/tasks.py
from huey.contrib.djhuey import task  # Декоратор для фоновых задач
from django.core.mail import EmailMessage  # Класс для работы с почтой
import logging  # Модуль для записи логов
from email.utils import formataddr  # Официальная библиотека Python для сборки email-заголовков

logger = logging.getLogger(__name__)

@task()
def send_async_email(subject, message, recipient_list, from_email=None, fail_silently=False, **kwargs):
    # Если передан один адрес строкой, делаем из него список
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]

    # Идеально правильное формирование заголовка по стандарту RFC 5322
    # Функция formataddr сама подставит нужные скобки и безопасно обработает текст
    sender = formataddr(('EsaEsTuCasa', 'info@esaestu.casa'))

    try:
        # Создаем письмо с нашим гарантированно правильным отправителем
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=sender,
            to=recipient_list,
        )
        # Отправляем письмо
        email.send(fail_silently=fail_silently)
        logger.info(f"Email sent to {recipient_list}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {str(e)}")