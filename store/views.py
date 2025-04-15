from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models import Q, Avg
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.mail import send_mail
from collections import defaultdict
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from store.tasks import send_order_status_update_email
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from store.utils import send_order_email

from .models import (
    Book, Genre, Author, Publisher, Category,
    Review, Cart as CartModel, CartItem,
    OrderItem, Order, Notification, Favorite, Profile, BookImage
)
from .forms import (
    OrderCreateForm, ReviewForm, UserRegisterForm,
    UserUpdateForm, ProfileUpdateForm, OrderUpdateForm
)

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET", "POST"])
def payment_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if order.status != 'pending' or order.is_paid:
        messages.warning(request, "Этот заказ уже оплачен или отменён.")
        return redirect('order_detail', pk=order.pk)

    cart_total = sum(item.price * item.quantity for item in order.items.all())
    final_total = cart_total - order.cashback_used

    if request.method == 'POST':
        # Обновляем заказ
        order.status = 'paid'
        order.is_paid = True
        order.save()

        # Уведомление
        Notification.objects.create(
            user=request.user,
            message=f'Оплата заказа №{order.pk} прошла успешно.'
        )

        # WebSocket уведомление
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{request.user.id}",
            {
                'type': 'send_notification',
                'message': f'Оплата заказа №{order.pk} прошла успешно.'
            }
        )

        # 📧 Отправляем письмо с актуальным статусом!
        send_order_email(order)

        return render(request, 'store/payment_success.html', {'order': order})

    return render(request, 'store/fake_payment.html', {
        'order': order,
        'final_total': final_total
    })

@login_required
@require_http_methods(["GET", "POST"])
def fake_payment(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if request.method == "POST":
        order.status = 'paid'
        order.is_paid = True
        order.save()

        Notification.objects.create(
            user=request.user,
            message=f'Ваш заказ №{order.pk} был успешно оплачен.'
        )

        messages.success(request, f'Заказ №{order.pk} оплачен.')
        return redirect('order_detail', pk=order.pk)

    return render(request, 'store/fake_payment.html', {'order': order})


@login_required
def payment_success(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'store/payment_success.html', {'order': order})


@login_required
def update_cart_item(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()
        except ValueError:
            pass

        cart = item.cart
        total_price = cart.get_total_price()

        return JsonResponse({
            'item_total': float(item.get_total_price()),
            'cart_total': float(total_price)
        })


@login_required
def order_thank_you(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'store/order_thank_you.html', {'order': order})

# --- AUTH ---

def logout_view(request):
    logout(request)
    return redirect('index')


# --- REGISTER ---

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            CartModel.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Вы успешно зарегистрировались!')
            return redirect('index')
    else:
        form = UserRegisterForm()
    return render(request, 'store/register.html', {'form': form})


# --- PROFILE ---

@login_required
def profile(request):
    orders = request.user.orders.prefetch_related('items__book').order_by('-created')
    profile = request.user.profile
    return render(request, 'store/profile.html', {
        'orders': orders,
        'cashback': profile.cashback
    })


def about_page(request):
    return render(request, 'store/pages/about.html')

def contacts_page(request):
    return render(request, 'store/pages/contacts.html')

def privacy_page(request):
    return render(request, 'store/pages/privacy.html')


@login_required
def edit_profile(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, 'store/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


# --- ORDERS ---

@login_required
def my_orders(request):
    orders = request.user.orders.prefetch_related('items__book').order_by('-created')

    orders_with_totals = []
    for order in orders:
        full_price = order.get_total_cost()
        final_price = full_price - order.cashback_used
        orders_with_totals.append({
            'order': order,
            'final_total': final_price
        })

    return render(request, 'store/my_orders.html', {
        'orders_with_totals': orders_with_totals
    })

@login_required
def edit_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if not order.can_be_cancelled():
        messages.error(request, "Заказ уже обрабатывается и не может быть изменён.")
        return redirect('order_detail', pk=order.pk)

    if request.method == 'POST':
        form = OrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()

            item_ids = request.POST.getlist('item_ids')
            for item_id in item_ids:
                try:
                    item = order.items.get(id=item_id)
                    quantity = int(request.POST.get(f'quantity_{item_id}', item.quantity))
                    if quantity > 0:
                        item.quantity = quantity
                        item.save()
                    else:
                        item.delete()
                except (OrderItem.DoesNotExist, ValueError):
                    continue

            send_mail(
                subject=f'Обновление заказа №{order.pk}',
                message='Ваш заказ был успешно обновлён. Вы можете проверить детали в личном кабинете.',
                from_email=None,
                recipient_list=[order.email],
                fail_silently=True,
            )

            Notification.objects.create(
                user=request.user,
                message=f'Ваш заказ №{order.pk} был обновлён.'
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{request.user.id}",
                {
                    'type': 'send_notification',
                    'message': f'Ваш заказ №{order.pk} был обновлён.'
                }
            )

            messages.success(request, f"Заказ №{order.pk} успешно обновлён.")
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderUpdateForm(instance=order)

    return render(request, 'store/order_edit.html', {'form': form, 'order': order})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    items = order.items.select_related('book')

    cart_total = sum(item.price * item.quantity for item in items)
    cashback_earned = sum(item.book.cashback * item.quantity for item in items)

    profile = request.user.profile
    cashback_used = getattr(order, 'cashback_used', 0)
    final_total = cart_total - cashback_used

    context = {
        'order': order,
        'items': items,
        'cart_total': cart_total,
        'cashback_used': cashback_used,
        'final_total': final_total,
        'cashback_earned': cashback_earned,
        'bonus_balance': profile.cashback,
    }
    return render(request, 'store/order_detail.html', context)

@login_required
def fake_payment(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if order.status == 'pending' and not order.is_paid:
        order.status = 'paid'
        order.is_paid = True
        order.save()

        Notification.objects.create(
            user=request.user,
            message=f"Заказ №{order.pk} был оплачен."
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{request.user.id}",
            {
                'type': 'send_notification',
                'message': f"Заказ №{order.pk} был оплачен."
            }
        )

        messages.success(request, f"Заказ №{order.pk} успешно оплачен.")
    else:
        messages.warning(request, f"Заказ №{order.pk} уже был оплачен или не может быть оплачен.")

    return redirect('order_detail', pk=order.pk)


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.can_be_cancelled():
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Заказ №{order.id} был отменён.')
    else:
        messages.error(request, 'Этот заказ нельзя отменить.')
    return redirect('my_orders')


# --- INDEX ---


def index(request):
    books = Book.objects.order_by('-created_at')[:8]
    catalog_books = Book.objects.all().order_by('?')[:8]
    return render(request, 'store/index.html', {
        'books': books,
        'catalog_books': catalog_books
    })


# --- CATALOG ---


def catalog(request):
    books = Book.objects.all()
    query = request.GET.get('q')
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(author__name__icontains=query)
        )

    genre_id = request.GET.get('genre')
    if genre_id and genre_id.isdigit():
        books = books.filter(genre_id=genre_id)

    author_id = request.GET.get('author')
    if author_id:
        books = books.filter(author_id=author_id)

    publisher_id = request.GET.get('publisher')
    if publisher_id:
        books = books.filter(publisher_id=publisher_id)

    sort = request.GET.get('sort')
    if sort == 'price_asc':
        books = books.order_by('price')
    elif sort == 'price_desc':
        books = books.order_by('-price')
    elif sort == 'title':
        books = books.order_by('title')
    elif sort == 'year':
        books = books.order_by('-year')

    categorized_genres = defaultdict(list)
    for genre in Genre.objects.select_related('category'):
        if genre.category:
            categorized_genres[genre.category.name].append(genre)

    paginator = Paginator(books, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'store/catalog.html', {
        'page_obj': page_obj,
        'genres': Genre.objects.all(),
        'authors': Author.objects.all(),
        'publishers': Publisher.objects.all(),
        'query': query,
        'genre_id': genre_id,
        'author_id': author_id,
        'publisher_id': publisher_id,
        'sort': sort,
        'categorized_genres': dict(categorized_genres)
    })

# --- BOOK DETAIL + REVIEWS ---


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.select_related('user').order_by('-created_at')
    images = BookImage.objects.filter(book=book)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    form = ReviewForm(request.POST or None)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(
                request, 'Только авторизованные пользователи могут оставлять отзывы.')
            return redirect('login')
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            try:
                review.save()
                messages.success(request, 'Спасибо за отзыв!')
                return redirect('book_detail', pk=book.pk)
            except:
                form.add_error(None, 'Вы уже оставляли отзыв к этой книге.')
    return render(request, 'store/book_detail.html', {
        'book': book,
        'form': form,
        'reviews': reviews,
        'images': images,
        'avg_rating': avg_rating
    })


# --- NOTIFICATIONS ---


@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(
        user=request.user).order_by('-created_at')
    user_notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'store/notifications.html', {'notifications': user_notifications})


# --- FAVORITES ---


@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(
        user=request.user).select_related('book')
    return render(request, 'store/favorites.html', {'favorites': favorites})


@login_required
def add_to_favorites(request, pk):
    book = get_object_or_404(Book, pk=pk)
    Favorite.objects.get_or_create(user=request.user, book=book)
    messages.success(request, f'«{book.title}» добавлена в избранное.')
    return redirect(request.META.get('HTTP_REFERER', 'index'))


@login_required
def remove_from_favorites(request, pk):
    Favorite.objects.filter(user=request.user, book__pk=pk).delete()
    messages.success(request, 'Книга удалена из избранного.')
    return redirect(request.META.get('HTTP_REFERER', 'index'))

# --- REVIEWS ---


@login_required
def my_reviews(request):
    reviews = request.user.reviews.select_related(
        'book').order_by('-created_at')
    return render(request, 'store/my_reviews.html', {'reviews': reviews})


@login_required
def edit_review(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    form = ReviewForm(request.POST or None, instance=review)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Отзыв обновлён.')
        return redirect('book_detail', pk=review.book.pk)
    return render(request, 'store/edit_review.html', {'form': form, 'review': review})


@login_required
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    book_pk = review.book.pk
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Отзыв удалён.')
        return redirect('book_detail', pk=book_pk)
    return render(request, 'store/delete_review.html', {'review': review})


# --- CART ---


@login_required
def add_to_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart, _ = CartModel.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, book=book)
    if not created:
        item.quantity += 1
    item.save()
    return redirect('cart_detail')


@login_required
def buy_now(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart, _ = CartModel.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, book=book)
    if not created:
        item.quantity += 1
    item.save()
    return redirect('order_create')


@login_required
def remove_from_cart(request, pk):
    cart = get_object_or_404(CartModel, user=request.user)
    CartItem.objects.filter(cart=cart, book__pk=pk).delete()
    return redirect('cart_detail')


@login_required
def cart_detail(request):
    cart = get_object_or_404(CartModel, user=request.user)
    items = cart.items.select_related('book')
    total_price = sum(item.get_total_price() for item in items)
    return render(request, 'store/cart.html', {
        'cart': cart,
        'items': items,
        'total_price': total_price,
    })

# --- ORDER CREATION ---


@login_required
def order_create(request):
    cart = get_object_or_404(CartModel, user=request.user)
    items = cart.items.select_related('book')
    profile = request.user.profile

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        use_cashback = request.POST.get('use_cashback') == 'on'

        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.email = form.cleaned_data['email']

            cart_total = cart.get_total_price()
            cashback_used = min(profile.cashback, cart_total) if use_cashback else 0
            final_total = cart_total - cashback_used

            order.cashback_used = cashback_used
            order.save()

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    book=item.book,
                    price=item.book.discounted_price,
                    quantity=item.quantity
                )

            cart.items.all().delete()

            if use_cashback:
                profile.cashback -= cashback_used

            total_cashback = sum(item.book.cashback * item.quantity for item in items)
            profile.cashback += total_cashback
            profile.save()

            # HTML-письмо с деталями заказа
            html_message = render_to_string('store/email/order_email.html', {
            'order': order,
            'items': items,
            'cart_total': cart_total,
            'cashback_used': cashback_used,
            'final_total': final_total,
            'cashback_earned': total_cashback,
            'bonus_balance': profile.cashback,  
          })

            plain_message = strip_tags(html_message)

            send_mail(
                subject=f'Подтверждение заказа №{order.id} в BookHive',
                message=plain_message,
                from_email='Shurik75328@gmail.com',
                recipient_list=[order.email],
                html_message=html_message,
                fail_silently=True,
            )

            send_order_status_update_email.delay(order.id)

            return redirect('payment_view', pk=order.pk)
    else:
        form = OrderCreateForm()

    return render(request, 'store/order_create.html', {
        'cart': cart,
        'form': form,
        'cashback': profile.cashback
    })

def discount_books(request):
    books = Book.objects.filter(discount__gt=0).order_by('-discount')
    return render(request, 'store/discount_books.html', {'books': books})
