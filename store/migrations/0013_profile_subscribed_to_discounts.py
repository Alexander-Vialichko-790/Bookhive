# Generated by Django 5.2 on 2025-04-13 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0012_order_comment_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='subscribed_to_discounts',
            field=models.BooleanField(default=False, verbose_name='Подписан на скидки'),
        ),
    ]
