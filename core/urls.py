from django.urls import path
from .views import home_view, page_detail, search_view

urlpatterns = [
    path('', home_view, name='home'),
    path('search/', search_view, name='search'),
    path('<slug:slug>/', page_detail, name='page_detail'),
    
]