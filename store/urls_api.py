from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    RegisterView, LogoutView,
    BookListAPIView, OrderListCreateAPIView,
    CartDetailAPIView, CartAddAPIView, CartRemoveAPIView,
    BookReviewListCreateAPIView, ReviewViewSet,
    TopBooksAnalyticsView, DailySalesAnalyticsView,
    NotificationViewSet, FavoriteViewSet, ProfileAPIView,
    
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'favorites', FavoriteViewSet, basename='favorites')

urlpatterns = [
    # JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User actions
    path('register/', RegisterView.as_view(), name='api-register'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Catalog and Orders
    path('books/', BookListAPIView.as_view(), name='api_books'),
    path('orders/', OrderListCreateAPIView.as_view(), name='api_orders'),

    # Cart
    path('cart/', CartDetailAPIView.as_view(), name='api_cart'),
    path('cart/add/', CartAddAPIView.as_view(), name='api_cart_add'),
    path('cart/remove/<int:pk>/', CartRemoveAPIView.as_view(), name='api_cart_remove'),

    # Reviews
    path('books/<int:book_id>/reviews/', BookReviewListCreateAPIView.as_view(), name='api_book_reviews'),

    # Analytics
    path('analytics/sales/', DailySalesAnalyticsView.as_view(), name='api_analytics_sales'),
    path('analytics/top-books/', TopBooksAnalyticsView.as_view(), name='api_top_books'),

    # Profile
    path('profile/', ProfileAPIView.as_view(), name='api_profile'),


    # Include registered ViewSets
    path('', include(router.urls)),
]
