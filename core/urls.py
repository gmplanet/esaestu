from django.urls import path
from .views import home_view, page_detail

urlpatterns = [
    # Главная страница теперь берет на себя и фильтрацию, и поиск
    path('', home_view, name='home'),
    path('<slug:slug>/', page_detail, name='page_detail'),
]