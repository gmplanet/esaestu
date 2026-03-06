from django.db import models
from django.urls import reverse
from django.db.models import Q
from django.utils.translation import get_language, activate
from django_ckeditor_5.fields import CKEditor5Field
from mptt.models import MPTTModel, TreeForeignKey # Импортируем базовый класс для древовидных моделей и специальное поле связи из библиотеки MPTT
from django.core.exceptions import ValidationError

# Модель страницы с поддержкой английского и испанского языков
class Page(models.Model):
    # Английский
    title_en = models.CharField(max_length=200, verbose_name="Title (EN)")
    # Используем CKEditor5Field для включения визуального редактора в интерфейсе админки
    # Параметр config_name='extends' связывает это поле с нашими настройками тулбара
    content_en = CKEditor5Field(verbose_name="Content (EN)", config_name='extends')
    slug_en = models.SlugField(max_length=200, unique=True, verbose_name="URL Slug (EN)")
    
    # Испанский
    title_es = models.CharField(max_length=200, verbose_name="Title (ES)")
    # Аналогично меняем поле для испанского контента
    content_es = CKEditor5Field(verbose_name="Content (ES)", config_name='extends')
    slug_es = models.SlugField(max_length=200, unique=True, verbose_name="URL Slug (ES)")
    
    # Метаданные
    @property
    def title(self):
        """Автоматически возвращает заголовок на текущем языке."""
        return self.title_es if get_language().startswith('es') else self.title_en
    
    @property
    def content(self):
        """Автоматически возвращает контент на текущем языке."""
        return self.content_es if get_language().startswith('es') else self.content_en
    
    # URL страницы
    def get_absolute_url(self):
        return self.get_url_for_lang(get_language())
    
    # Генерация URL для указанного языка
    def get_url_for_lang(self, lang_code):
        old_lang = get_language()
        try:
            activate(lang_code)
            # Выбираем правильный слаг для генерации URL
            slug = self.slug_es if lang_code.startswith('es') else self.slug_en
            return reverse('page_detail', kwargs={'slug': slug})
        finally:
            activate(old_lang)
    
    # Поиск страниц по запросу
    @staticmethod
    def search(query):
        return Page.objects.filter(
            Q(title_en__icontains=query) | 
            Q(content_en__icontains=query) |
            Q(title_es__icontains=query) |
            Q(content_es__icontains=query)
        ).distinct()

    def __str__(self):
        return self.title_en
    
    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"

# Модель элемента меню с поддержкой иерархии и ссылок на страницы или внешние URL
class MenuItem(MPTTModel):
    title_en = models.CharField(max_length=100, verbose_name="Title (EN)")
    title_es = models.CharField(max_length=100, verbose_name="Title (ES)")
    
    # Заменяем стандартный ForeignKey на TreeForeignKey для правильной работы алгоритмов MPTT
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, 
        related_name='children', verbose_name="Parent Item"
    )
    linked_page = models.ForeignKey(
        'Page', on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='menu_items', verbose_name="Linked Page"
    )
    url = models.CharField(max_length=200, blank=True, null=True, verbose_name="External URL")
    order = models.PositiveIntegerField(default=0, verbose_name="Order")

    @property
    def title(self):
        """Умное поле заголовка для меню."""
        return self.title_es if get_language().startswith('es') else self.title_en

    # Убираем стандартную сортировку (ordering), так как MPTT использует собственные алгоритмы выстраивания дерева
    class Meta:
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"

    # Добавляем специальный класс настроек для MPTT
    class MPTTMeta:
        # Указываем, по какому полю сортировать элементы на одном уровне дерева (соседей)
        order_insertion_by = ['order']

    def __str__(self):
        return f"↳ {self.title}" if self.parent else self.title

    def get_url(self):
        if self.linked_page:
            return self.linked_page.get_absolute_url()
        return self.url if self.url else "#"
    
    def clean(self):
        # Обязательно вызываем базовый метод валидации перед нашими собственными проверками
        super().clean()
        
        # Проверяем, назначен ли текущему пункту меню родительский элемент
        if self.parent:
            # Алгоритм отслеживает глубину автоматически в поле level.
            # Если выбранный родитель уже находится на уровне 2 (это третий уровень вложенности) или глубже,
            # мы блокируем сохранение, так как наш новый пункт стал бы четвертым уровнем.
            if self.parent.level >= 3:
                # Генерируем ошибку, которая прервет сохранение и подсветит поле 'parent' красным текстом в админке
                raise ValidationError({'parent': 'Максимальная глубина вложенности меню — 3 уровня.'})

# Модель для управления режимом обслуживания сайта
class Maintenance(models.Model):
    is_active = models.BooleanField(default=False, verbose_name="Is Maintenance Active?")
    message_en = models.TextField(verbose_name="Message (EN)")
    message_es = models.TextField(verbose_name="Message (ES)")

    @property
    def message(self):
        return self.message_es if get_language().startswith('es') else self.message_en

    class Meta:
        verbose_name = "Maintenance Mode"
        verbose_name_plural = "Maintenance Mode"

# Модель для хранения текста футера с поддержкой двух языков
class Footer(models.Model):
    text_en = models.TextField(verbose_name="Footer Text (EN)")
    text_es = models.TextField(verbose_name="Footer Text (ES)")

    @property
    def text(self):
        return self.text_es if get_language().startswith('es') else self.text_en

    class Meta:
        verbose_name = "Footer"
        verbose_name_plural = "Footer"