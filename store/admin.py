from django.contrib import admin
from .models import (
    Book, BookImage, Author, Genre, Publisher,
    Order, OrderItem,
    Profile, Notification, Favorite, Review,
    Cart, CartItem
)
from .tasks import send_order_status_update_email
# admin.py
from django.contrib import admin
from django import forms
from django.shortcuts import render, redirect
import csv
from io import TextIOWrapper
from .models import Category, Genre

class CSVImportForm(forms.Form):
    csv_file = forms.FileField()

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    change_list_template = "admin/genre_changelist.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path("import-csv/", self.import_csv)
        ]
        return custom_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            decoded_file = TextIOWrapper(csv_file, encoding="utf-8")
            reader = csv.DictReader(decoded_file)

            for row in reader:
                category_name = row["category_name"].strip()
                genre_name = row["genre_name"].strip()

                category, _ = Category.objects.get_or_create(name=category_name)
                Genre.objects.get_or_create(name=genre_name, category=category)

            self.message_user(request, "Жанры успешно импортированы")
            return redirect("..")

        form = CSVImportForm()
        return render(request, "admin/csv_form.html", {"form": form})


# --- Inline изображения книг ---
class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 1

# --- Книга ---
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'genre', 'price', 'status', 'discount', 'cashback']
    list_filter = ['genre', 'author', 'status']
    search_fields = ['title', 'description']
    inlines = [BookImageInline]

# --- Прочие модели ---
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ['name']

# --- Заказ и его товары ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'is_paid', 'created']
    list_filter = ['status', 'is_paid', 'created']
    search_fields = ['user__username', 'user__email']
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        send_order_status_update_email.delay(obj.id)

# --- Остальные модели ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'added_at']
    list_filter = ['added_at']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['text']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'book', 'quantity']
