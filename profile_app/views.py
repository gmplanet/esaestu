# profile_app/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
# Импортируем logout для выхода из системы перед удалением
from django.contrib.auth import get_user_model, logout
# Импортируем нашу новую форму настроек
from .forms import UserProfileForm

User = get_user_model()

@login_required
def cabinet_view(request):
    # Если метод POST, пользователь отправил форму (нажал одну из кнопок)
    if request.method == 'POST':
        # Получаем значение скрытого поля action, чтобы понять, что именно нужно сделать
        action = request.POST.get('action')
        
        # Обработка обновления профиля
        if action == 'update_profile':
            form = UserProfileForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect('cabinet')
                
        # Обработка удаления аккаунта
        elif action == 'delete_account':
            user = request.user
            # Сначала принудительно завершаем сессию
            logout(request)
            # Затем физически удаляем пользователя из базы данных
            user.delete()
            # Перенаправляем на главную страницу сайта
            return redirect('/')
            
    # Если это обычный переход по ссылке (GET-запрос)
    else:
        # Загружаем форму с текущими сохраненными данными пользователя
        form = UserProfileForm(instance=request.user)

    return render(request, 'profile_app/cabinet.html', {
        'user': request.user,
        'form': form
    })

def public_profile_view(request, slug):
    profile_user = get_object_or_404(User, slug=slug)
    return render(request, 'profile_app/public_profile.html', {
        'profile_user': profile_user
    })