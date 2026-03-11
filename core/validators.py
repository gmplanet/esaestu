# core/validators.py
import magic
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_is_image(file):
    """
    Проверяет первые байты файла (magic numbers), чтобы определить реальный тип контента.
    """
    # Допустимые MIME-типы
    valid_mime_types = ['image/jpeg', 'image/png', 'image/webp']
    
    # Считываем начало файла для анализа
    file_content = file.read(2048)
    file.seek(0) # Возвращаем указатель в начало, чтобы файл можно было сохранить позже
    
    # Определяем MIME-тип
    mime_type = magic.from_buffer(file_content, mime=True)
    
    if mime_type not in valid_mime_types:
        raise ValidationError(
            _('Unsupported file type: %(type)s. Please upload a valid JPEG, PNG or WEBP image.'),
            params={'type': mime_type},
        )