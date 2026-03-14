# shop_app/admin.py
from django.contrib import admin
from .models import (
    Product, ProductImage, ProductOption, ProductOptionValue,
    Cart, CartItem, Order, OrderItem, OrderComment, SellerAccess
)

# Инлайн-модели для удобного отображения картинок и вариаций прямо внутри товара
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductOptionValueInline(admin.TabularInline):
    model = ProductOptionValue
    extra = 1

class ProductOptionAdmin(admin.ModelAdmin):
    inlines = [ProductOptionValueInline]
    list_display = ['name', 'product']

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ['title', 'owner', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'owner__username']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'price', 'quantity', 'selected_options']

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ['order_number', 'buyer', 'seller', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_email']

class SellerAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'can_add_multiple_images', 'can_add_variants']
    search_fields = ['user__username', 'user__email']

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductOption, ProductOptionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(SellerAccess, SellerAccessAdmin)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderComment)