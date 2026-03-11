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
from .models import Product, ProductImage, Cart, CartItem, Order, OrderItem, OrderComment
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
                        quantity=actual_quantity
                    )
                    order_details_text += f" - {item.product.title}: {actual_quantity} шт.\n"
            
            cart_items.delete()
            
            # Уведомления (используем order.uuid для ссылок в будущем или order_number для текста)
            buyer_subject = _("Your order #%(order_id)s from %(seller)s") % {'order_id': order.order_number, 'seller': seller.username}
            buyer_message = _("Hello! Your order #%(order_id)s has been sent to %(seller)s.") % {'order_id': order.order_number, 'seller': seller.username}
            
            try:
                send_async_email(buyer_subject, buyer_message, [order.customer_email])
                send_async_email(_("New order #%(id)s") % {'id': order.order_number}, "New order details...", [seller.email])
            except Exception:
                pass
                
            return redirect('public_shop', slug=slug)
    else:
        initial_data = {'customer_name': request.user.username, 'customer_email': request.user.email}
        form = CheckoutForm(initial=initial_data)
        
    return render(request, 'shop_app/checkout.html', {
        'form': form, 'seller': seller, 'cart_items': cart_items, 'cart_total': cart_total
    })

@login_required
def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        new_quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product=product)

        if new_quantity > cart_item.quantity and new_quantity > product.stock:
            return JsonResponse({'status': 'error', 'message': _('Not enough stock.')}, status=400)
        
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
        
        try:
            send_async_email(_("Order Update"), f"Status: {new_status}", [order.buyer.email])
        except Exception:
            pass
            
    return redirect('shop_order_detail', order_uuid=order.uuid)

@require_POST
@login_required
def shop_cancel_order(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)
    
    if request.user != order.buyer and request.user != order.seller:
        raise PermissionDenied()
        
    if order.status in ['active', 'processing']:
        # Определяем, кто отменил заказ для уведомления
        is_buyer = request.user == order.buyer
        order.status = 'cancelled_by_buyer' if is_buyer else 'cancelled_by_seller'
        order.save()
        
        # 1. Формируем список товаров для письма
        items_list = ""
        for item in order.items.all():
            items_list += f"• {item.product_name} x {item.quantity}\n"
            
        # 2. Подготавливаем данные для письма
        subject = _("Order Cancelled: #%(number)s") % {'number': order.order_number}
        
        canceler_text = _("buyer") if is_buyer else _("seller")
        
        message = _(
            "Order #%(number)s from %(date)s has been cancelled by the %(canceler)s.\n\n"
            "Order details:\n"
            "%(items)s\n"
            "Status: %(status)s"
        ) % {
            'number': order.order_number,
            'date': order.created_at.strftime('%Y-%m-%d'),
            'canceler': canceler_text,
            'items': items_list,
            'status': order.get_status_display()
        }

        try:
            send_async_email(
                subject, 
                message, 
                settings.DEFAULT_FROM_EMAIL, 
                [order.buyer.email, order.seller.email], 
                fail_silently=True
            )
        except Exception:
            pass
            
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
        try:
            send_async_email(_("New Message"), safe_comment, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=True)
        except Exception:
            pass
            
    return redirect('shop_order_detail', order_uuid=order.uuid)