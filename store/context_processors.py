from .models import Cart
from collections import defaultdict
from .models import Genre
from .models import Favorite
from .models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'notification_count': count}
    return {}

def favorites_count(request):
    if request.user.is_authenticated:
        return {'favorites_count': Favorite.objects.filter(user=request.user).count()}
    return {'favorites_count': 0}

def cart_context(request):
    if request.user.is_authenticated:
        try:
            user_cart = Cart.objects.prefetch_related('items__book').get(user=request.user)
            item_count = sum(item.quantity for item in user_cart.items.all())
        except Cart.DoesNotExist:
            user_cart = Cart.objects.create(user=request.user)
            item_count = 0
        return {
            'cart': user_cart,
            'cart_items_count': item_count
        }
    return {'cart': None, 'cart_items_count': 0}


def categorized_genres(request):
    grouped = defaultdict(list)
    for genre in Genre.objects.select_related('category'):
        if genre.category:
            grouped[genre.category.name].append(genre)
    return {'categorized_genres': dict(grouped)}
