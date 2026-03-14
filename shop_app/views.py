# shop_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from core.tasks import send_async_email
from django.conf import settings
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from django.db.models import Q
from django_ratelimit.decorators import ratelimit
# Добавили ProductOption и ProductOptionValue в импорты
from .models import Product, ProductImage, ProductOption, ProductOptionValue, Cart, CartItem, Order, OrderItem, OrderComment
from .forms import ProductForm, CheckoutForm
from django.contrib import messages
from django.urls import reverse
from django.middleware.csrf import get_token
import json

User = get_user_model()

@login_required
def cabinet_shop_list(request):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
    
    products = Product.objects.filter(owner=request.user)
    return render(request, 'shop_app/cabinet_product_list.html', {'products': products})

@login_required
def cabinet_shop_add(request):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
        
    current_product_count = Product.objects.filter(owner=request.user).count()
    if current_product_count >= request.user.sku_limit:
        return redirect('cabinet_shop_list')

    # Проверяем права пользователя
    has_multi_image_access = hasattr(request.user, 'shop_access') and request.user.shop_access.can_add_multiple_images
    has_variant_access = hasattr(request.user, 'shop_access') and request.user.shop_access.can_add_variants
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            
            images = request.FILES.getlist('images')
            if not has_multi_image_access and images:
                images = images[:1] 
                
            for idx, image in enumerate(images):
                is_main = True if idx == 0 else False
                ProductImage.objects.create(product=product, image=image, is_main=is_main)
            
            # Сохраняем опции товара, если есть права
            if has_variant_access:
                option_names = request.POST.getlist('option_names')
                option_values = request.POST.getlist('option_values')
                
                for name, values_str in zip(option_names, option_values):
                    name = name.strip()
                    values_str = values_str.strip()
                    if name and values_str:
                        # Создаем категорию опции (например, "Размер")
                        option = ProductOption.objects.create(product=product, name=name)
                        # Разбиваем строку "S, M, L" по запятым и сохраняем каждое значение
                        vals = [v.strip() for v in values_str.split(',') if v.strip()]
                        for v in vals:
                            ProductOptionValue.objects.create(option=option, value=v)
                
            return redirect('cabinet_shop_list')
    else:
        form = ProductForm()
        
    return render(request, 'shop_app/cabinet_product_add.html', {
        'form': form,
        'has_multi_image_access': has_multi_image_access,
        'has_variant_access': has_variant_access
    })

def public_shop_view(request, slug):
    shop_owner = get_object_or_404(User, slug=slug)
    products = Product.objects.filter(owner=shop_owner, is_active=True).prefetch_related('options__values')
    
    cart_items_count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart, product__owner=shop_owner)
        cart_items_count = sum(item.quantity for item in cart_items)

    js_config = {
        'translations': {
            'clickToClose': str(_('Click anywhere to close')),
        }
    }

    return render(request, 'shop_app/public_shop.html', {
        'shop_owner': shop_owner,
        'products': products,
        'cart_items_count': cart_items_count,
        'js_config': js_config,
    })

def public_product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    shop_owner = product.owner
    
    cart_items_count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart, product__owner=shop_owner)
        cart_items_count = sum(item.quantity for item in cart_items)

    js_config = {
        'translations': {
            'clickToClose': str(_('Click anywhere to close')),
        }
    }

    return render(request, 'shop_app/public_product_detail.html', {
        'product': product,
        'shop_owner': shop_owner,
        'cart_items_count': cart_items_count,
        'js_config': js_config,
    })

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        if product.owner == request.user:
            messages.error(request, _("You cannot buy your own products."))
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        selected_options = {}
        for key, value in request.POST.items():
            if key.startswith('option_'):
                option_name = key.replace('option_', '')
                selected_options[option_name] = value
                
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item = CartItem.objects.filter(cart=cart, product=product, selected_options=selected_options).first()
        
        MAX_QTY_PER_ITEM = 15 
        
        if cart_item:
            if cart_item.quantity < product.stock and cart_item.quantity < MAX_QTY_PER_ITEM:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, _("Item added to cart."))
            else:
                messages.warning(request, _("Maximum quantity reached for this item."))
        else:
            if product.stock > 0:
                CartItem.objects.create(cart=cart, product=product, quantity=1, selected_options=selected_options)
                messages.success(request, _("Item added to cart."))
                
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def cabinet_shop_delete(request, product_id):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    if request.method == 'POST':
        product.delete()
        return redirect('cabinet_shop_list')
    return render(request, 'shop_app/cabinet_product_confirm_delete.html', {'product': product})

@login_required
def cabinet_shop_edit(request, product_id):
    if not request.user.is_seller:
        raise PermissionDenied("You do not have permission to access this page.")
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    
    has_multi_image_access = hasattr(request.user, 'shop_access') and request.user.shop_access.can_add_multiple_images
    has_variant_access = hasattr(request.user, 'shop_access') and request.user.shop_access.can_add_variants
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            images = request.FILES.getlist('images')
            if images:
                if not has_multi_image_access:
                    images = images[:1]
                    
                product.images.all().delete()
                for idx, image in enumerate(images):
                    is_main = True if idx == 0 else False
                    ProductImage.objects.create(product=product, image=image, is_main=is_main)
            
            # Обновляем опции товара (удаляем старые и создаем новые)
            if has_variant_access:
                product.options.all().delete()
                option_names = request.POST.getlist('option_names')
                option_values = request.POST.getlist('option_values')
                
                for name, values_str in zip(option_names, option_values):
                    name = name.strip()
                    values_str = values_str.strip()
                    if name and values_str:
                        option = ProductOption.objects.create(product=product, name=name)
                        vals = [v.strip() for v in values_str.split(',') if v.strip()]
                        for v in vals:
                            ProductOptionValue.objects.create(option=option, value=v)
                            
            return redirect('cabinet_shop_list')
    else:
        form = ProductForm(instance=product)
        
    return render(request, 'shop_app/cabinet_product_edit.html', {
        'form': form, 
        'product': product,
        'has_multi_image_access': has_multi_image_access,
        'has_variant_access': has_variant_access
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

@login_required
def shop_cart_view(request, slug):
    shop_owner = get_object_or_404(User, slug=slug)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart, product__owner=shop_owner)
    
    if not cart_items.exists():
        messages.info(request, _("Your cart in this shop is empty."))
        return redirect('public_shop', slug=slug)
        
    cart_total = sum(item.total_price for item in cart_items)
    js_config = {
        'updateCartUrlBase': reverse('update_cart_quantity', args=[0]).replace('0/', ''),
        'csrfToken': get_token(request),
        'translations': {
            'errorUpdating': str(_('Error updating cart.')),
        }
    }
    return render(request, 'shop_app/shop_cart.html', {
        'shop_owner': shop_owner, 'cart_items': cart_items, 'cart_total': cart_total, 'js_config': js_config,
    })

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
@login_required
def checkout_view(request, slug):
    seller = get_object_or_404(User, slug=slug)
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart, product__owner=seller)
    
    if not cart_items.exists():
        return redirect('public_shop', slug=slug)
        
    cart_total = sum(item.total_price for item in cart_items)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.buyer = request.user
            order.seller = seller
            order.save()
            
            order_details_text = ""
            for item in cart_items:
                actual_quantity = min(item.quantity, item.product.stock)
                if actual_quantity > 0:
                    item.product.stock -= actual_quantity
                    item.product.save()
                    
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.title,
                        price=item.product.price,
                        quantity=actual_quantity,
                        selected_options=item.selected_options
                    )
                    
                    # Форматируем опции: каждый товар с новой строки (\n)
                    options_str = ""
                    if item.selected_options:
                        options_str = " (" + ", ".join([f"{k}: {v}" for k, v in item.selected_options.items()]) + ")"
                    
                    order_details_text += f"\n- {item.product.title}{options_str}: {actual_quantity} unit"
            
            cart_items.delete()
            
            buyer_subject = _("Your order #%(order_id)s from %(seller)s") % {'order_id': order.order_number, 'seller': seller.username}
            buyer_message = _(
                "Hello %(buyer_name)s!\n\n"
                "Your order #%(order_id)s has been successfully placed and sent to %(seller)s.\n\n"
                "Order Details:\n%(items)s\nTotal Price: $%(total)s\n\nThank you for your purchase!"
            ) % {'buyer_name': order.customer_name, 'order_id': order.order_number, 'seller': seller.username, 'items': order_details_text, 'total': cart_total}
            
            seller_subject = _("New order #%(id)s from %(buyer)s") % {'id': order.order_number, 'buyer': order.customer_name}
            seller_message = _(
                "Hello %(seller_name)s!\n\n"
                "You have received a new order #%(order_id)s.\n\n"
                "Customer Information:\nName: %(buyer_name)s\nEmail: %(buyer_email)s\n\n"
                "Order Details:\n%(items)s\nTotal Amount: $%(total)s\n\nPlease check your personal cabinet to process this order."
            ) % {'seller_name': seller.username, 'order_id': order.order_number, 'buyer_name': order.customer_name, 'buyer_email': order.customer_email, 'items': order_details_text, 'total': cart_total}
            
            try:
                send_async_email(buyer_subject, buyer_message, [order.customer_email])
                send_async_email(seller_subject, seller_message, [seller.email])
            except Exception as e:
                print(f"Checkout email error: {e}") 

            success_msg = _(
                "Order #%(order_id)s confirmed successfully!\n\nItems:\n%(items)s\nTotal Amount: $%(total)s"
            ) % {'order_id': order.order_number, 'items': order_details_text, 'total': cart_total}
            
            messages.success(request, success_msg)    
            return redirect('public_shop', slug=slug)
    else:
        initial_data = {'customer_name': request.user.username, 'customer_email': request.user.email}
        form = CheckoutForm(initial=initial_data)
        
    return render(request, 'shop_app/checkout.html', {
        'form': form, 'seller': seller, 'cart_items': cart_items, 'cart_total': cart_total
    })

@login_required
def update_cart_quantity(request, item_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_quantity = int(data.get('quantity', 1))
        
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        product = cart_item.product

        MAX_QTY_PER_ITEM = 15
        
        if new_quantity > MAX_QTY_PER_ITEM or (new_quantity > cart_item.quantity and new_quantity > product.stock):
            return JsonResponse({
                'status': 'error', 
                'message': str(_('Maximum quantity reached for this item.'))
            }, status=400)
        
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
            cart_total = sum(item.total_price for item in CartItem.objects.filter(cart=cart, product__owner=product.owner))
            return JsonResponse({'status': 'success', 'item_total': float(cart_item.total_price), 'cart_total': float(cart_total)})
        else:
            cart_item.delete()
            return JsonResponse({'status': 'deleted'})

@login_required
def cabinet_my_orders(request):
    orders = Order.objects.filter(buyer=request.user)
    counts = {
        'new': orders.filter(status='active').count(),
        'processing': orders.filter(status='processing').count(),
        'completed': orders.filter(status='completed').count(),
        'cancelled': orders.filter(status__in=['cancelled_by_buyer', 'cancelled_by_seller']).count(),
    }
    
    current_tab = request.GET.get('tab', 'new')
    if current_tab == 'new': orders = orders.filter(status='active')
    elif current_tab == 'processing': orders = orders.filter(status='processing')
    elif current_tab == 'completed': orders = orders.filter(status='completed')
    elif current_tab == 'cancelled': orders = orders.filter(status__in=['cancelled_by_buyer', 'cancelled_by_seller'])
    
    query = request.GET.get('q', '')
    if query:
        orders = orders.filter(Q(order_number__icontains=query) | Q(seller__username__icontains=query))
    
    sort_by = request.GET.get('sort', '-created_at')
    orders = orders.order_by(sort_by if sort_by in ['created_at', '-created_at'] else '-created_at')
    
    return render(request, 'shop_app/cabinet_my_orders.html', {
        'orders': orders, 'counts': counts, 'current_tab': current_tab, 'query': query, 'sort_by': sort_by,
    })

@login_required
def cabinet_incoming_orders(request):
    if not request.user.is_seller:
        raise PermissionDenied()
        
    orders = Order.objects.filter(seller=request.user)
    counts = {
        'new': orders.filter(status='active').count(),
        'processing': orders.filter(status='processing').count(),
        'completed': orders.filter(status='completed').count(),
        'cancelled': orders.filter(status__in=['cancelled_by_buyer', 'cancelled_by_seller']).count(),
    }
    
    current_tab = request.GET.get('tab', 'new')
    if current_tab == 'new': orders = orders.filter(status='active')
    elif current_tab == 'processing': orders = orders.filter(status='processing')
    elif current_tab == 'completed': orders = orders.filter(status='completed')
    elif current_tab == 'cancelled': orders = orders.filter(status__in=['cancelled_by_buyer', 'cancelled_by_seller'])
    
    query = request.GET.get('q', '')
    if query:
        orders = orders.filter(Q(order_number__icontains=query) | Q(customer_name__icontains=query))
        
    sort_by = request.GET.get('sort', '-created_at')
    orders = orders.order_by(sort_by)
    
    return render(request, 'shop_app/cabinet_incoming_orders.html', {
        'orders': orders, 'counts': counts, 'current_tab': current_tab, 'query': query, 'sort_by': sort_by,
    })

@login_required
def shop_order_detail(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)
    if request.user != order.buyer and request.user != order.seller:
        raise PermissionDenied()
    return render(request, 'shop_app/cabinet_order_detail.html', {'order': order})

@require_POST
@login_required
def shop_update_order_status(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)
    if request.user != order.seller:
        raise PermissionDenied()
        
    new_status = request.POST.get('status')
    if new_status in ['processing', 'completed']:
        order.status = new_status
        order.save()
        
        subject = _("Order #%(id)s Status Update") % {'id': order.order_number}
        message = _(
            "Hello %(buyer_name)s!\n\n"
            "The status of your order #%(order_id)s has been updated to: %(status)s.\n\n"
            "Thank you!"
        ) % {'buyer_name': order.customer_name, 'order_id': order.order_number, 'status': order.get_status_display()}
        
        try:
            send_async_email(subject, message, [order.buyer.email])
        except Exception as e:
            print(f"Update status email error: {e}")
            
    return redirect('shop_order_detail', order_uuid=order.uuid)

@require_POST
@login_required
def shop_cancel_order(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)
    if request.user != order.buyer and request.user != order.seller:
        raise PermissionDenied()
        
    if order.status in ['active', 'processing']:
        is_buyer = request.user == order.buyer
        order.status = 'cancelled_by_buyer' if is_buyer else 'cancelled_by_seller'
        order.save()
        
        items_list = ""
        for item in order.items.all():
            options_str = ""
            if item.selected_options:
                options_str = " (" + ", ".join([f"{k}: {v}" for k, v in item.selected_options.items()]) + ")"
            items_list += f"• {item.product_name}{options_str} x {item.quantity}\n"
            
        subject = _("Order Cancelled: #%(number)s") % {'number': order.order_number}
        canceler_text = _("buyer") if is_buyer else _("seller")
        
        message = _(
            "Hello!\n\n"
            "Order #%(number)s from %(date)s has been cancelled by the %(canceler)s.\n\n"
            "Order details:\n%(items)s\nFinal Status: %(status)s"
        ) % {'number': order.order_number, 'date': order.created_at.strftime('%Y-%m-%d'), 'canceler': canceler_text, 'items': items_list, 'status': order.get_status_display()}

        try:
            send_async_email(subject, message, [order.buyer.email, order.seller.email])
        except Exception as e:
            print(f"Cancel order email error: {e}")
            
    return redirect('shop_order_detail', order_uuid=order.uuid)

@require_POST
@login_required
def shop_add_comment(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)
    if request.user != order.buyer and request.user != order.seller:
        raise PermissionDenied()
        
    comment_text = request.POST.get('comment_text', '')
    safe_comment = strip_tags(comment_text)[:250]
    
    if safe_comment:
        OrderComment.objects.create(order=order, author=request.user, text=safe_comment)
        recipient = order.seller.email if request.user == order.buyer else order.buyer.email
        
        subject = _("New comment on order #%(id)s") % {'id': order.order_number}
        message = _(
            "Hello!\n\n"
            "A new comment has been added to order #%(order_id)s by %(author)s:\n\n"
            "\"%(comment)s\"\n\n"
            "Please check your personal cabinet to view and reply."
        ) % {'order_id': order.order_number, 'author': request.user.username, 'comment': safe_comment}
        
        try:
            send_async_email(subject, message, [recipient])
        except Exception as e:
            print(f"Add comment email error: {e}")
            
    return redirect('shop_order_detail', order_uuid=order.uuid)