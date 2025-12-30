from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailVerifiedBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        if user:
            # Если пароль верный, но почта не подтверждена — возвращаем None (вход запрещен)
            if not user.is_email_verified:
                return None
        return user