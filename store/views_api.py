from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.contrib.auth.models import User
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Book
from .serializers import BookSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    Book, Author, Publisher, Genre, Order, OrderItem,
    Cart, CartItem, Review, Notification, Favorite, Profile
)
from .serializers import (
    BookSerializer, AuthorSerializer, PublisherSerializer, GenreSerializer,
    OrderSerializer, OrderItemSerializer, CartSerializer, CartItemSerializer,
    ReviewSerializer, NotificationSerializer, FavoriteSerializer,
    ProfileSerializer, RegisterSerializer, DailySalesSerializer, TopBooksSerializer
)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.all().select_related('author', 'genre', 'publisher')
    serializer_class = BookSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['genre__category__id', 'genre__id', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at', 'year']
    ordering = ['-created_at']


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookListAPIView(generics.ListAPIView):
    queryset = Book.objects.all().select_related('author', 'publisher', 'genre')
    serializer_class = BookSerializer

class OrderListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__book')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, email=self.request.user.email)

class CartDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

class CartAddAPIView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        book_id = request.data.get("book")
        quantity = int(request.data.get("quantity", 1))
        cart, _ = Cart.objects.get_or_create(user=request.user)
        book = Book.objects.get(id=book_id)
        item, created = CartItem.objects.get_or_create(cart=cart, book=book)
        item.quantity = item.quantity + quantity if not created else quantity
        item.save()
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)

class CartRemoveAPIView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        cart = Cart.objects.get(user=request.user)
        item = CartItem.objects.filter(cart=cart, id=pk).first()
        if item:
            item.delete()
            return Response({"detail": "Item removed."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

class BookReviewListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.filter(book_id=self.kwargs['book_id'])

    def perform_create(self, serializer):
        if Review.objects.filter(book_id=self.kwargs['book_id'], user=self.request.user).exists():
            raise ValidationError("Вы уже оставили отзыв на эту книгу.")
        serializer.save(user=self.request.user, book_id=self.kwargs['book_id'])

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('book', 'user').all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if Review.objects.filter(book=serializer.validated_data['book'], user=self.request.user).exists():
            raise ValidationError("Вы уже оставили отзыв для этой книги.")
        serializer.save(user=self.request.user)

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('book')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        favorite = self.get_object()
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'Уведомление прочитано'})

class DailySalesAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        data = (
            Order.objects.filter(is_paid=True)
            .annotate(date=TruncDate('created'))
            .values('date')
            .annotate(total_orders=Sum('id'), total_amount=Sum('cashback_used'))
        )
        serializer = DailySalesSerializer(data, many=True)
        return Response(serializer.data)

class TopBooksAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        data = (
            OrderItem.objects
            .values('book_id', 'book__title')
            .annotate(total_quantity=Sum('quantity'), total_earned=Sum('price'))
            .order_by('-total_quantity')[:5]
        )
        serializer = TopBooksSerializer(data, many=True)
        return Response(serializer.data)
