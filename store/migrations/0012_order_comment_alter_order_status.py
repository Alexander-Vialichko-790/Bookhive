# Generated by Django 5.2 on 2025-04-12 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0011_alter_profile_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, verbose_name='Комментарий к заказу'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Ожидает'), ('paid', 'Оплачен'), ('shipped', 'В пути'), ('delivered', 'Доставлен'), ('cancelled', 'Отменён')], default='pending', max_length=20, verbose_name='Статус'),
        ),
    ]
