from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from .views_api import FavoriteViewSet
from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('order/create/', views.order_create, name='order_create'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path('review/<int:pk>/edit/', views.edit_review, name='edit_review'),
    path('review/<int:pk>/delete/', views.delete_review, name='delete_review'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('favorites/add/<int:pk>/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/<int:pk>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('notifications/', views.notifications, name='notifications'),
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('cancel-order/<int:pk>/', views.cancel_order, name='cancel_order'),
    path('buy-now/<int:pk>/', views.buy_now, name='buy_now'),
    path('cart/update/<int:pk>/', views.update_cart_item, name='update_cart_item'),
    path('order/<int:pk>/edit/', views.edit_order, name='edit_order'),
    path('discounts/', views.discount_books, name='discount_books'),
    path('order/<int:pk>/pay/', views.fake_payment, name='fake_payment'),
    path('order/<int:pk>/payment/', views.payment_view, name='payment_view'),
    path('order/<int:pk>/thank-you/', views.order_thank_you, name='order_thank_you'),
    path('order/<int:pk>/payment/success/', views.payment_success, name='payment_success'),
    path('about/', TemplateView.as_view(template_name="pages/about.html"), name='about'),
    path('contacts/', TemplateView.as_view(template_name="pages/contacts.html"), name='contacts'),
    path('privacy/', TemplateView.as_view(template_name="pages/privacy.html"), name='privacy'),
]

# Добавляем API-роуты в конце
urlpatterns += router.urls
