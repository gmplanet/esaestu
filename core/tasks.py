# core/tasks.py
from huey.contrib.djhuey import task  # Декоратор для фоновых задач
from django.core.mail import EmailMessage  # Класс для работы с почтой
from django.conf import settings  # Доступ к настройкам проекта
import logging  # Модуль для записи логов

logger = logging.getLogger(__name__)

@task()
def send_async_email(subject, message, recipient_list, from_email=None, fail_silently=False, **kwargs):
    # Если передан один адрес строкой, делаем из него список
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]

    # Получаем чистый адрес из настроек (например, info@esaestu.casa)
    raw_email = from_email or settings.DEFAULT_FROM_EMAIL
    # На всякий случай счищаем случайные кавычки
    clean_email = raw_email.replace('"', '').replace("'", "")

    # ЖЕСТКО ПРОПИСЫВАЕМ ИМЯ ОТПРАВИТЕЛЯ ЗДЕСЬ
    # Собираем строку вида: Esaestu <info@esaestu.casa>
    sender = f"Esaestu <{clean_email}>"

    try:
        # Создаем письмо с нашим форматированным отправителем
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