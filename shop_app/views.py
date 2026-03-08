# shop_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext as _

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