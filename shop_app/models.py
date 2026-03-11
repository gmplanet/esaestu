# shop_app/models.py
from django.db import models
from django.contrib.auth import get_user_model
# ВАЖНО: Добавлен недостающий импорт для работы с картинками
from PIL import Image
from core.validators import validate_is_image
import uuid
import string
import secrets


# Получаем актуальную модель пользователя, чтобы связать товары с их владельцами
User = get_user_model()

# Модель для хранения информации о товаре
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

# Модель для хранения изображений товара
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


# ==========================================
# НОВЫЕ МОДЕЛИ ДЛЯ КОРЗИНЫ
# ==========================================

class Cart(models.Model):
    # У каждого пользователя (покупателя) строго одна корзина (OneToOneField)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="Customer")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(models.Model):
    # Привязка конкретной позиции к корзине пользователя
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Cart")
    # Ссылка на сам товар
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Product")
    # Количество этого товара в корзине
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Эта настройка не дает положить один и тот же товар в корзину двумя разными строками. 
        # Если товар уже есть, мы будем просто увеличивать quantity.
        unique_together = ('cart', 'product')
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.title} (Cart: {self.cart.user.username})"

    # Удобное свойство для получения итоговой суммы за эту позицию (цена * количество)
    @property
    def total_price(self):
        return self.product.price * self.quantity
    
# ==========================================
# НОВЫЕ МОДЕЛИ ДЛЯ ЗАКАЗОВ (Checkout)
# ==========================================
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
        # Используем order_number, если он есть, иначе старый добрый id
        return f"Order #{self.order_number or self.id} from {self.customer_name}"
    
    def generate_order_number(self):
        # Генерирует строку типа 'KJ8D32PL91WS'
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(12))

    def save(self, *args, **kwargs):
        if not self.order_number:
            new_number = self.generate_order_number()
            # Проверка на уникальность
            while Order.objects.filter(order_number=new_number).exists():
                new_number = self.generate_order_number()
            self.order_number = new_number
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    # Связь конкретной позиции с общим заказом
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Order")
    # Связь с исходным товаром (on_delete=models.SET_NULL сохранит историю заказа, если продавец в будущем удалит этот товар)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Product")
    
    # Копия названия и цены на момент покупки (цены могут меняться, история чека должна быть неизменной)
    product_name = models.CharField(max_length=200, verbose_name="Product Name Snapshot")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price Snapshot")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Order #{self.order.id})"

    @property
    def total_price(self):
        return self.price * self.quantity    
    

class OrderComment(models.Model):
    # Привязка комментария к конкретному заказу
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='comments', verbose_name="Order")
    # Кто именно написал комментарий (продавец или покупатель)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Author")
    # Текст комментария с жестким ограничением в 250 символов на уровне структуры базы данных
    text = models.TextField(max_length=250, verbose_name="Comment Text")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        # Сортируем комментарии по дате создания (старые сверху, новые снизу)
        ordering = ['created_at']
        verbose_name = "Order Comment"
        verbose_name_plural = "Order Comments"

    def __str__(self):
        return f"Comment by {self.author.username} on Order #{self.order.id}"    