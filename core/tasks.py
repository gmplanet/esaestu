# core/tasks.py
from huey.contrib.djhuey import task  # Импортируем декоратор для превращения функции в фоновую задачу
from django.core.mail import EmailMessage  # Используем класс EmailMessage для гибкого управления заголовками письма
from django.conf import settings  # Импортируем глобальные настройки проекта
import logging  # Импортируем встроенную библиотеку логирования

# Создаем объект логгера для текущего модуля
logger = logging.getLogger(__name__)

@task()  # Указываем Huey, что эта функция должна выполняться асинхронно в фоновом режиме
def send_async_email(subject, message, recipient_list, from_email=None, fail_silently=False, **kwargs):
    # Проверяем, передан ли получатель как строка, и преобразуем в список, если это так
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]

    # Определяем адрес отправителя: берем переданный в функцию или используем глобальный из настроек
    sender = from_email or settings.DEFAULT_FROM_EMAIL

    # Очищаем строку от лишних кавычек, которые могли буквально прочитаться из файла .env
    if isinstance(sender, str):
        sender = sender.replace('"', '').replace("'", "")

    try:
        # Инициализируем объект письма с необходимыми параметрами
        email = EmailMessage(
            subject=subject,  # Заголовок письма
            body=message,  # Основной текстовый контент письма
            from_email=sender,  # Адрес и имя отправителя в формате Имя <email>
            to=recipient_list,  # Список адресов получателей
        )

        # Выполняем физическую отправку письма через SMTP-сервер
        email.send(fail_silently=fail_silently)

        # Записываем в системный журнал информацию об успешной отправке
        logger.info(f"Email sent to {recipient_list}")
    except Exception as e:
        # Если произошла ошибка, записываем её в лог для последующего анализа
        logger.error(f"Failed to send email to {recipient_list}: {str(e)}")