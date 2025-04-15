from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from store.models import Order

@shared_task
def send_order_status_update_email(order_id):
    try:
        order = Order.objects.get(id=order_id)
        user = order.user

        subject = f'Обновление статуса заказа №{order.id}'
        message = f'Здравствуйте, {user.first_name or user.username}!\n\n' \
                  f'Статус вашего заказа обновлён: {order.get_status_display()}.\n\n' \
                  f'Спасибо, что выбрали BookHive!'

        send_mail(
            subject,
            message,
            None,  # из settings.DEFAULT_FROM_EMAIL
            [user.email],
            fail_silently=False
        )
    except Order.DoesNotExist:
        pass

@shared_task
def send_weekly_discount_emails():
    from store.models import Book, Profile
    from django.core.mail import send_mail

    discounted_books = Book.objects.filter(discount__gt=0)[:5]  # первые 5 со скидкой
    if not discounted_books:
        return

    book_list = "\n".join(
        [f"- {book.title} ({book.discount}%) — {book.discounted_price} ₽" for book in discounted_books]
    )

    subject = "🔥 Новые скидки в BookHive!"
    message = f"Привет! Вот список книг со скидкой:\n\n{book_list}\n\nЗагляни на сайт, пока всё не разобрали!"

    for profile in Profile.objects.filter(subscribed_to_discounts=True).select_related('user'):
        if profile.user.email:
            send_mail(
                subject,
                message,
                None,
                [profile.user.email],
                fail_silently=True
            )


from celery import shared_task
from datetime import datetime

@shared_task
def ping():
    print(f"[{datetime.now()}] 🔔 Ping от Celery. Всё работает!")

