# shop_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Управление товарами (кабинет продавца)
    path('cabinet/shop/', views.cabinet_shop_list, name='cabinet_shop_list'),
    path('cabinet/shop/add/', views.cabinet_shop_add, name='cabinet_shop_add'),
    path('cabinet/shop/delete/<int:product_id>/', views.cabinet_shop_delete, name='cabinet_shop_delete'),
    path('cabinet/shop/edit/<int:product_id>/', views.cabinet_shop_edit, name='cabinet_shop_edit'),
    path('cabinet/shop/toggle/<int:product_id>/', views.cabinet_shop_toggle_active, name='cabinet_shop_toggle_active'),
    
    # Публичная часть магазина
    path('u/<slug:slug>/shop/', views.public_shop_view, name='public_shop'),
    
    # НОВЫЙ МАРШРУТ: Отдельная карточка товара для подробного просмотра и выбора опций
    path('shop/product/<int:product_id>/', views.public_product_detail, name='public_product_detail'),
    
    # Корзина и оформление заказа
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    # ОБНОВЛЕННЫЙ МАРШРУТ: Теперь принимает item_id вместо product_id для корректной работы с вариациями
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('u/<slug:slug>/shop/cart/', views.shop_cart_view, name='shop_cart'),
    path('u/<slug:slug>/shop/checkout/', views.checkout_view, name='checkout'),

    # Управление заказами (кабинет)
    path('cabinet/shop/my-orders/', views.cabinet_my_orders, name='cabinet_my_orders'),
    path('cabinet/shop/incoming-orders/', views.cabinet_incoming_orders, name='cabinet_incoming_orders'),
    path('cabinet/shop/order/<uuid:order_uuid>/cancel/', views.shop_cancel_order, name='shop_cancel_order'),
    path('cabinet/shop/order/<uuid:order_uuid>/comment/', views.shop_add_comment, name='shop_add_comment'),
    path('cabinet/shop/order/<uuid:order_uuid>/', views.shop_order_detail, name='shop_order_detail'),
    path('cabinet/shop/order/<uuid:order_uuid>/update-status/', views.shop_update_order_status, name='shop_update_order_status'),
]