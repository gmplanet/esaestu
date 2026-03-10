# shop_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from .models import Order, OrderComment
from django.db.models import Q

# Импортируем наши новые модели и форму
from .models import Product, ProductImage, Cart, CartItem, Order, OrderItem
from .forms import ProductForm, CheckoutForm

User = get_user_model()

@login_required
def cabinet_shop_list(request):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
    
    products = Product.objects.filter(owner=request.user)
    
    return render(request, 'shop_app/cabinet_product_list.html', {
        'products': products
    })

@login_required
def cabinet_shop_add(request):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
        
    current_product_count = Product.objects.filter(owner=request.user).count()
    
    if current_product_count >= request.user.sku_limit:
        return redirect('cabinet_shop_list')
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            
            images = request.FILES.getlist('images')
            for idx, image in enumerate(images):
                is_main = True if idx == 0 else False
                ProductImage.objects.create(product=product, image=image, is_main=is_main)
                
            return redirect('cabinet_shop_list')
    else:
        form = ProductForm()
        
    return render(request, 'shop_app/cabinet_product_add.html', {
        'form': form
    })

def public_shop_view(request, slug):
    shop_owner = get_object_or_404(User, slug=slug)
    products = Product.objects.filter(owner=shop_owner, is_active=True)
    
    cart_items = []
    cart_total = 0

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart, product__owner=shop_owner)
        cart_total = sum(item.total_price for item in cart_items)

    return render(request, 'shop_app/public_shop.html', {
        'shop_owner': shop_owner,
        'products': products,
        'cart_items': cart_items,
        'cart_total': cart_total
    })

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        
        if cart_item:
            if cart_item.quantity < product.stock:
                cart_item.quantity += 1
                cart_item.save()
        else:
            if product.stock > 0:
                CartItem.objects.create(cart=cart, product=product, quantity=1)
                
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def cabinet_shop_delete(request, product_id):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
    
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    
    if request.method == 'POST':
        product.delete()
        return redirect('cabinet_shop_list')
        
    return render(request, 'shop_app/cabinet_product_confirm_delete.html', {
        'product': product
    })

@login_required
def cabinet_shop_edit(request, product_id):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
    
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            images = request.FILES.getlist('images')
            if images:
                product.images.all().delete()
                for idx, image in enumerate(images):
                    is_main = True if idx == 0 else False
                    ProductImage.objects.create(product=product, image=image, is_main=is_main)
            return redirect('cabinet_shop_list')
    else:
        form = ProductForm(instance=product)
        
    return render(request, 'shop_app/cabinet_product_edit.html', {
        'form': form,
        'product': product
    })

@login_required
def cabinet_shop_toggle_active(request, product_id):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
    
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    
    if request.method == 'POST':
        product.is_active = not product.is_active
        product.save()
        
    return redirect('cabinet_shop_list')

# ==========================================
# НОВАЯ ФУНКЦИЯ: ОФОРМЛЕНИЕ ЗАКАЗА
# ==========================================
@login_required
def checkout_view(request, slug):
    # Находим продавца, у которого совершается покупка
    seller = get_object_or_404(User, slug=slug)
    
    # Получаем корзину покупателя и фильтруем только товары этого продавца
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart, product__owner=seller)
    
    # Если корзина пуста (например, пользователь зашел по прямой ссылке), возвращаем в магазин
    if not cart_items.exists():
        return redirect('public_shop', slug=slug)
        
    cart_total = sum(item.total_price for item in cart_items)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # 1. Сохраняем заказ в базу данных
            order = form.save(commit=False)
            order.buyer = request.user
            order.seller = seller
            order.save()
            
            order_details_text = ""
            
            # 2. Переносим товары из корзины в OrderItem и вычитаем остатки со склада
            for item in cart_items:
                # На всякий случай проверяем, не раскупили ли товар, пока пользователь оформлял заказ
                actual_quantity = min(item.quantity, item.product.stock)
                
                if actual_quantity > 0:
                    # Вычитаем со склада
                    item.product.stock -= actual_quantity
                    item.product.save()
                    
                    # Создаем запись в чеке
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.title,
                        price=item.product.price,
                        quantity=actual_quantity
                    )
                    
                    # Формируем текст для письма
                    order_details_text += f" - {item.product.title}: {actual_quantity} шт.\n"
            
            # 3. Очищаем корзину покупателя от товаров этого продавца
            cart_items.delete()
            
            # 4. Отправляем email-уведомления
            # Письмо покупателю
            buyer_subject = _("Your order #%(order_id)s from %(seller)s") % {'order_id': order.id, 'seller': seller.username}
            buyer_message = _(
                "Your order (number %(order_id)s), from %(date)s, has been sent to the seller %(seller)s. "
                "Wait for them to contact you or contact the seller directly.\n\n"
                "Products:\n%(details)s\n"
                "Total Cost: $%(total)s"
            ) % {
                'order_id': order.id,
                'date': order.created_at.strftime('%Y-%m-%d'),
                'seller': seller.username,
                'details': order_details_text,
                'total': cart_total
            }
            
            # Письмо продавцу
            seller_subject = _("New order #%(order_id)s") % {'order_id': order.id}
            seller_message = _(
                "New order (number %(order_id)s)\n\n"
                "Products:\n%(details)s\n"
                "Total Cost: $%(total)s\n\n"
                "Customer: %(name)s\n"
                "Phone: %(phone)s\n"
                "Email: %(email)s\n"
                "Additional Info: %(info)s"
            ) % {
                'order_id': order.id,
                'details': order_details_text,
                'total': cart_total,
                'name': order.customer_name,
                'phone': order.customer_phone,
                'email': order.customer_email,
                'info': order.additional_info
            }
            
            try:
                # fail_silently=True предотвращает падение сайта, если SMTP-сервер пока не настроен
                send_mail(buyer_subject, buyer_message, settings.DEFAULT_FROM_EMAIL, [order.customer_email], fail_silently=True)
                send_mail(seller_subject, seller_message, settings.DEFAULT_FROM_EMAIL, [seller.email], fail_silently=True)
            except Exception:
                pass
                
            # Перенаправляем обратно в магазин продавца
            return redirect('public_shop', slug=slug)
    else:
        # Предзаполняем форму данными текущего пользователя для удобства
        initial_data = {
            'customer_name': request.user.username,
            'customer_email': request.user.email,
        }
        form = CheckoutForm(initial=initial_data)
        
    return render(request, 'shop_app/checkout.html', {
        'form': form,
        'seller': seller,
        'cart_items': cart_items,
        'cart_total': cart_total
    })


# проверка остатков на складе при изменении количества товара в корзине (AJAX)
@login_required
def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        new_quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product=product)

        # ЛОГИКА ПРОВЕРКИ:
        # Если пользователь УВЕЛИЧИВАЕТ количество, проверяем склад.
        # Если УМЕНЬШАЕТ, проверка склада не нужна.
        if new_quantity > cart_item.quantity:
            if new_quantity > product.stock:
                return JsonResponse({
                    'status': 'error', 
                    'message': _('Not enough stock. Available: %(stock)s') % {'stock': product.stock}
                }, status=400)
        
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
            
            shop_owner = product.owner
            cart_items = CartItem.objects.filter(cart=cart, product__owner=shop_owner)
            cart_total = sum(item.total_price for item in cart_items)

            return JsonResponse({
                'status': 'success',
                'item_total': float(cart_item.total_price),
                'cart_total': float(cart_total)
            })
        else:
            # Если дошли до 0, удаляем товар из корзины
            cart_item.delete()
            return JsonResponse({'status': 'deleted'})
        


# Контроллер для отображения покупок клиента (таблица и вкладки)
@login_required
def cabinet_my_orders(request):
    orders = Order.objects.filter(buyer=request.user)
    
    # Подсчет количества заказов для каждой вкладки
    counts = {
        'new': orders.filter(status='active').count(),
        'processing': orders.filter(status='processing').count(),
        'completed': orders.filter(status='completed').count(),
        'cancelled': orders.filter(status__in=['cancelled_by_buyer', 'cancelled_by_seller']).count(),
    }
    
    # Определение текущей вкладки (по умолчанию 'new')
    current_tab = request.GET.get('tab', 'new')
    if current_tab == 'new':
        orders = orders.filter(status='active')
    elif current_tab == 'processing':
        orders = orders.filter(status='processing')
    elif current_tab == 'completed':
        orders = orders.filter(status='completed')
    elif current_tab == 'cancelled':
        orders = orders.filter(status__in=['cancelled_by_buyer', 'cancelled_by_seller'])
        
    # Обработка поиска
    query = request.GET.get('q', '')
    if query:
        orders = orders.filter(
            Q(id__icontains=query) |
            Q(seller__username__icontains=query)
        )
        
    # Обработка сортировки
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['created_at', '-created_at', 'id', '-id']:
        orders = orders.order_by(sort_by)
    else:
        orders = orders.order_by('-created_at')
        
    return render(request, 'shop_app/cabinet_my_orders.html', {
        'orders': orders,
        'counts': counts,
        'current_tab': current_tab,
        'query': query,
        'sort_by': sort_by,
    })

# Контроллер для отображения входящих заказов продавца (таблица и вкладки)
@login_required
def cabinet_incoming_orders(request):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
        
    orders = Order.objects.filter(seller=request.user)
    
    counts = {
        'new': orders.filter(status='active').count(),
        'processing': orders.filter(status='processing').count(),
        'completed': orders.filter(status='completed').count(),
        'cancelled': orders.filter(status__in=['cancelled_by_buyer', 'cancelled_by_seller']).count(),
    }
    
    current_tab = request.GET.get('tab', 'new')
    if current_tab == 'new':
        orders = orders.filter(status='active')
    elif current_tab == 'processing':
        orders = orders.filter(status='processing')
    elif current_tab == 'completed':
        orders = orders.filter(status='completed')
    elif current_tab == 'cancelled':
        orders = orders.filter(status__in=['cancelled_by_buyer', 'cancelled_by_seller'])
        
    query = request.GET.get('q', '')
    if query:
        # Для продавца ищем по имени, email, телефону покупателя или номеру заказа
        orders = orders.filter(
            Q(id__icontains=query) |
            Q(customer_name__icontains=query) |
            Q(customer_email__icontains=query) |
            Q(customer_phone__icontains=query)
        )
        
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['created_at', '-created_at', 'id', '-id']:
        orders = orders.order_by(sort_by)
    else:
        orders = orders.order_by('-created_at')
        
    return render(request, 'shop_app/cabinet_incoming_orders.html', {
        'orders': orders,
        'counts': counts,
        'current_tab': current_tab,
        'query': query,
        'sort_by': sort_by,
    })

# Новый контроллер для страницы с деталями конкретного заказа и чатом
@login_required
def shop_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Проверка прав (доступ только для участников сделки)
    if request.user != order.buyer and request.user != order.seller:
        raise PermissionDenied("You do not have permission to view this order.")
        
    return render(request, 'shop_app/cabinet_order_detail.html', {'order': order})


# Новый контроллер для изменения статуса продавцом (в работу / выполнен)
@require_POST
@login_required
def shop_update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.user != order.seller:
        raise PermissionDenied("Only the seller can change this status.")
        
    new_status = request.POST.get('status')
    if new_status in ['processing', 'completed']:
        order.status = new_status
        order.save()
        
        # Отправка уведомления покупателю
        status_text = "Processing" if new_status == 'processing' else "Completed"
        subject = _("Order Update: #%(id)s is now %(status)s") % {'id': order.id, 'status': status_text}
        message = _(
            "Hello %(buyer)s,\n\n"
            "The status of your order #%(id)s has been updated to: %(status)s.\n\n"
            "You can view the details in your account."
        ) % {
            'buyer': order.buyer.username,
            'id': order.id,
            'status': status_text
        }
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.buyer.email], fail_silently=True)
        except Exception:
            pass
            
    return redirect('shop_order_detail', order_id=order.id)


# Контроллер для отмены заказа (оставляем старый, но обновляем редирект)
@require_POST
@login_required
def shop_cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    is_buyer = request.user == order.buyer
    is_seller = request.user == order.seller
    
    if not (is_buyer or is_seller):
        raise PermissionDenied("You cannot cancel this order.")
        
    if order.status not in ['active', 'processing']:
        return redirect('shop_order_detail', order_id=order.id)
        
    if is_buyer:
        order.status = 'cancelled_by_buyer'
        canceler = "Buyer"
    else:
        order.status = 'cancelled_by_seller'
        canceler = "Seller"
        
    order.save()
    
    subject = _("Order Cancelled: #%(id)s") % {'id': order.id}
    message = _("Order #%(id)s has been cancelled by the %(canceler)s.\n\n") % {'id': order.id, 'canceler': canceler}
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.buyer.email, order.seller.email], fail_silently=True)
    except Exception:
        pass
        
    return redirect('shop_order_detail', order_id=order.id)

# Контроллер для добавления комментария (оставляем старый, редирект обновлен)
@require_POST
@login_required
def shop_add_comment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.user != order.buyer and request.user != order.seller:
        raise PermissionDenied("You cannot comment on this order.")
        
    comment_text = request.POST.get('comment_text', '')
    safe_comment = strip_tags(comment_text)[:250]
    
    if safe_comment:
        OrderComment.objects.create(order=order, author=request.user, text=safe_comment)
        recipient_email = order.seller.email if request.user == order.buyer else order.buyer.email
        subject = _("New comment on Order #%(id)s") % {'id': order.id}
        message = _("You have a new comment on Order #%(id)s from %(author)s:\n\n%(comment)s") % {'id': order.id, 'author': request.user.username, 'comment': safe_comment}
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=True)
        except Exception:
            pass
            
    return redirect('shop_order_detail', order_id=order.id)      