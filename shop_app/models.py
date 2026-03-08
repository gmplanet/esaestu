# shop_app/models.py
from django.db import models
from django.contrib.auth import get_user_model
# ВАЖНО: Добавлен недостающий импорт для работы с картинками
from PIL import Image

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
    # Привязка заказа к покупателю и продавцу для масштабируемости
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_as_buyer', verbose_name="Buyer")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_as_seller', verbose_name="Seller")

    # Контактные данные покупателя из формы оформления
    customer_name = models.CharField(max_length=100, verbose_name="Customer Name")
    customer_phone = models.CharField(max_length=50, verbose_name="Customer Phone")
    customer_email = models.EmailField(verbose_name="Customer Email")
    # Ограничение в 500 символов реализовано через max_length
    additional_info = models.TextField(max_length=500, blank=True, verbose_name="Additional Info")

    # Дата создания заказа будет использоваться как часть информации для писем
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        # Идентификатор self.id будет выступать в роли номера заказа
        return f"Order #{self.id} from {self.customer_name}"

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