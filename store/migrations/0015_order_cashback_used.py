# Generated by Django 5.1.8 on 2025-04-14 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0014_profile_cashback'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='cashback_used',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
