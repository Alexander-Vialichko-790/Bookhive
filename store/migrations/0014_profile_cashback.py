# Generated by Django 5.1.8 on 2025-04-14 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0013_profile_subscribed_to_discounts'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='cashback',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Кэшбэк'),
        ),
    ]
