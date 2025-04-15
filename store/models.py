from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend


# models.py

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Категория")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']


class Genre(models.Model):
    name = models.CharField(max_length=100, verbose_name="Жанр")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория", null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"
        ordering = ['name']


class Author(models.Model):
    name = models.CharField(max_length=150, verbose_name="Автор")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"
        ordering = ['name']


class Publisher(models.Model):
    name = models.CharField(max_length=150, verbose_name="Издательство")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Издательство"
        verbose_name_plural = "Издательства"
        ordering = ['name']


class Book(models.Model):
    STATUS_CHOICES = [
        ('in_stock', 'В наличии'),
        ('preorder', 'Под заказ'),
        ('out_of_stock', 'Нет в наличии')
    ]

    title = models.CharField(max_length=255, verbose_name="Название")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name="Автор")
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, verbose_name="Жанр")
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, verbose_name="Издательство")
    description = models.TextField(verbose_name="Описание")
    year = models.PositiveIntegerField(verbose_name="Год издания")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(upload_to='books/', default='books/placeholder.jpg', verbose_name="Обложка")
    discount = models.PositiveIntegerField(default=0, verbose_name="Скидка (%)")
    cashback = models.PositiveIntegerField(default=0, verbose_name="Кэшбэк (₽)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock', verbose_name="Наличие")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("book_detail", args=[self.pk])

    @property
    def discounted_price(self):
        if self.discount:
            discounted = self.price * (Decimal(100) - Decimal(self.discount)) / Decimal(100)
            return discounted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return self.price

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ['-created_at']


class BookImage(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='images', verbose_name="Книга")
    image = models.ImageField(upload_to='books/gallery/', verbose_name="Фото книги")

    def __str__(self):
        return f"Фото для {self.book.title}"

    class Meta:
        verbose_name = "Фото книги"
        verbose_name_plural = "Галерея книг"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="Пользователь")

    def __str__(self):
        return f"Корзина {self.user.username}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Корзина")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Книга")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        return f"{self.book.title} × {self.quantity}"

    def get_total_price(self):
        return self.book.discounted_price * self.quantity

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"
        unique_together = ('cart', 'book')


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('paid', 'Оплачен'),
        ('shipped', 'В пути'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Пользователь")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.CharField(max_length=250, verbose_name="Адрес доставки")
    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    is_paid = models.BooleanField(default=False, verbose_name="Оплачен")
    cashback_used = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    def __str__(self):
        return f'Заказ #{self.id} от {self.first_name}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def can_be_cancelled(self):
        return self.status == 'pending' and not self.is_paid

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Заказ")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Книга")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        return f'{self.book.title} ({self.quantity} шт.)'

    def get_cost(self):
        return self.price * self.quantity

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name="Книга")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="Пользователь")
    text = models.TextField(verbose_name="Отзыв", max_length=1000)
    rating = models.PositiveSmallIntegerField(verbose_name="Оценка", choices=[(i, str(i)) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отзыва")

    def __str__(self):
        return f'{self.user.username} → {self.book.title} ({self.rating})'

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        constraints = [
            models.UniqueConstraint(fields=['book', 'user'], name='unique_review')
        ]
        ordering = ['-created_at']


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Пользователь")
    message = models.CharField(max_length=255, verbose_name="Сообщение")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return f"Уведомление для {self.user.username}: {self.message}"

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="Пользователь")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='favorited_by', verbose_name="Книга")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    def __str__(self):
        return f"{self.user.username} ❤ {self.book.title}"

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='unique_favorite')
        ]
        ordering = ['-added_at']


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    photo = models.ImageField(upload_to='avatars/', blank=True, null=True)
    subscribed_to_discounts = models.BooleanField(default=False, verbose_name="Подписан на скидки")
    cashback = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Кэшбэк")

    def __str__(self):
        return f"Профиль {self.user.username}"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

