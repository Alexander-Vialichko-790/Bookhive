from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order

def send_order_email(order):
    # Вычисляем значения для шаблона
    items = order.items.all()
    cart_total = sum(item.price * item.quantity for item in items)
    final_total = cart_total - order.cashback_used
    cashback_earned = sum(item.book.cashback for item in items)
    bonus_balance = order.user.profile.cashback

    # Контекст для шаблона
    context = {
        'order': order,
        'items': items,
        'cart_total': cart_total,
        'final_total': final_total,
        'cashback_used': order.cashback_used,
        'cashback_earned': cashback_earned,
        'bonus_balance': bonus_balance,
    }

    # Генерируем письмо
    subject = f"Подтверждение оплаты заказа №{order.pk}"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [order.email]

    html_content = render_to_string('emails/order_email.html', context)

    msg = EmailMultiAlternatives(subject, html_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
