from .models import Cart, CartItem, Book

def get_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

def add_to_cart(user, book_id, quantity=1):
    cart = get_user_cart(user)
    book = Book.objects.get(id=book_id)
    item, created = CartItem.objects.get_or_create(cart=cart, book=book)
    if not created:
        item.quantity += quantity
    item.save()

def remove_from_cart(user, book_id):
    cart = get_user_cart(user)
    CartItem.objects.filter(cart=cart, book_id=book_id).delete()

def clear_cart(user):
    cart = get_user_cart(user)
    cart.items.all().delete()
