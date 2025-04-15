from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .cart import Cart as SessionCart
from .models import Cart, CartItem, Profile


@receiver(user_logged_in)
def merge_carts_on_login(sender, request, user, **kwargs):
    session_cart = SessionCart(request)

    if len(session_cart) == 0:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)

    for item in session_cart:
        book = item.get('book')
        quantity = item.get('quantity', 1)

        if book is None:
            continue

        cart_item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            book=book,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

    session_cart.clear()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
