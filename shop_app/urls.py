# shop_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Маршрут для просмотра списка товаров в кабинете продавца. Имя маршрута используем для ссылок в шаблонах
    path('cabinet/shop/', views.cabinet_shop_list, name='cabinet_shop_list'),
    
    # Маршрут для страницы добавления нового товара
    path('cabinet/shop/add/', views.cabinet_shop_add, name='cabinet_shop_add'),
    
    # Маршрут для удаления существующего товара
    path('cabinet/shop/delete/<int:product_id>/', views.cabinet_shop_delete, name='cabinet_shop_delete'),
    
    # Маршрут для редактирования существующего товара
    path('cabinet/shop/edit/<int:product_id>/', views.cabinet_shop_edit, name='cabinet_shop_edit'),
    
    # Маршрут для переключения статуса активности товара (виден/скрыт)
    path('cabinet/shop/toggle/<int:product_id>/', views.cabinet_shop_toggle_active, name='cabinet_shop_toggle_active'),
    
    # Маршрут для отображения публичной витрины магазина по уникальному слагу продавца
    path('u/<slug:slug>/shop/', views.public_shop_view, name='public_shop'),
    
    # Маршрут для добавления конкретного товара в корзину пользователя
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    # Новый маршрут для страницы оформления заказа (Checkout)
    path('u/<slug:slug>/shop/checkout/', views.checkout_view, name='checkout'),

    # Маршрут для обновления количества товара в корзине (AJAX)
    path('cart/update/<int:product_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    # Маршрут для удаления товара из корзины
    path('cabinet/shop/my-orders/', views.cabinet_my_orders, name='cabinet_my_orders'),
    # Маршрут для просмотра входящих заказов продавцом
    path('cabinet/shop/incoming-orders/', views.cabinet_incoming_orders, name='cabinet_incoming_orders'),
    # Маршрут для отмены заказа покупателем
    path('cabinet/shop/order/<int:order_id>/cancel/', views.shop_cancel_order, name='shop_cancel_order'),
    # Маршрут для добавления комментария к заказу (после завершения)
    path('cabinet/shop/order/<int:order_id>/comment/', views.shop_add_comment, name='shop_add_comment'),
    # Маршрут для просмотра деталей конкретного заказа продавцом и покупателем  
    path('cabinet/shop/order/<int:order_id>/', views.shop_order_detail, name='shop_order_detail'),
    # Маршрут для обновления статуса заказа продавцом (например, пометить как "выполнен" или "отменен")
    path('cabinet/shop/order/<int:order_id>/update-status/', views.shop_update_order_status, name='shop_update_order_status'),
]