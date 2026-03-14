# shop_app/models.py
from django.db import models
from django.contrib.auth import get_user_model
from PIL import Image
from core.validators import validate_is_image
import uuid
import string
import secrets

User = get_user_model()

# ==========================================
# ПРАВА ДОСТУПА ДЛЯ ПРОДАВЦОВ (Управляется Админом)
# ==========================================
class SellerAccess(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop_access', verbose_name="Seller")
    can_add_multiple_images = models.BooleanField(default=False, verbose_name="Can add multiple images")
    can_add_variants = models.BooleanField(default=False, verbose_name="Can add product variants (color, size)")

    class Meta:
        verbose_name = "Seller Access Right"
        verbose_name_plural = "Seller Access Rights"

    def __str__(self):
        return f"Access settings for {self.user.username}"


# ==========================================
# ТОВАРЫ И ИХ АТРИБУТЫ
# ==========================================
class Product(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', verbose_name="Owner")
    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(blank=True, verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Product")
    image = models.ImageField(upload_to='shop_images/%Y/%m/%d/', verbose_name="Image")
    is_main = models.BooleanField(default=False, verbose_name="Main Image")
    validators=[validate_is_image]

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image for {self.product.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.width > 400:
            new_width = 400
            new_height = int((new_width / img.width) * img.height)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img.save(self.image.path)

# Название характеристики (например, "Размер" или "Цвет")
class ProductOption(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='options')
    name = models.CharField(max_length=50, verbose_name="Option Name (e.g. Color)")

    def __str__(self):
        return f"{self.product.title} - {self.name}"

# Варианты характеристики (например, "Красный", "XL")
class ProductOptionValue(models.Model):
    option = models.ForeignKey(ProductOption, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=50, verbose_name="Value (e.g. Red)")

    def __str__(self):
        return self.value


# ==========================================
# КОРЗИНА И ЗАКАЗЫ
# ==========================================
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="Customer")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Cart")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Product")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    
    # НОВОЕ: Сохраняем выбранные опции в виде JSON (например: {"Color": "Red", "Size": "M"})
    selected_options = models.JSONField(default=dict, blank=True, verbose_name="Selected Options")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    @property
    def total_price(self):
        return self.product.price * self.quantity
    
class Order(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order_number = models.CharField(max_length=12, unique=True, editable=False, null=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_as_buyer', verbose_name="Buyer")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_as_seller', verbose_name="Seller")
    customer_name = models.CharField(max_length=100, verbose_name="Customer Name")
    customer_phone = models.CharField(max_length=50, verbose_name="Customer Phone")
    customer_email = models.EmailField(verbose_name="Customer Email")
    additional_info = models.TextField(max_length=500, blank=True, verbose_name="Additional Info")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    STATUS_CHOICES = [
        ('active', 'New'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled_by_buyer', 'Cancelled by Buyer'),
        ('cancelled_by_seller', 'Cancelled by Seller'),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active', verbose_name="Status")

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number or self.id} from {self.customer_name}"
    
    def generate_order_number(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(12))

    def save(self, *args, **kwargs):
        if not self.order_number:
            new_number = self.generate_order_number()
            while Order.objects.filter(order_number=new_number).exists():
                new_number = self.generate_order_number()
            self.order_number = new_number
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Order")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Product")
    product_name = models.CharField(max_length=200, verbose_name="Product Name Snapshot")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price Snapshot")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    
    # НОВОЕ: Сохраняем выбранные опции для истории заказа
    selected_options = models.JSONField(default=dict, blank=True, verbose_name="Selected Options Snapshot")

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def total_price(self):
        return self.price * self.quantity    

class OrderComment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='comments', verbose_name="Order")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Author")
    text = models.TextField(max_length=250, verbose_name="Comment Text")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Order Comment"
        verbose_name_plural = "Order Comments"