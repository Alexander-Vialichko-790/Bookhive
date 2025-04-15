from .models import Cart

class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=user)
            request.cart = cart  # чтобы использовать в представлениях
        return self.get_response(request)
    