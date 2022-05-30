# Generated by Django 3.2 on 2022-05-30 13:20

from django.db import migrations
from django.db.migrations import RunPython


def set_default_payment_status(apps, schema_editor):
    Order = apps.get_model('foodcartapp', 'Order')
    orders = Order.objects.filter(payment_type__isnull=True)
    orders.update(payment_type='cash')


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0050_order_payment_type'),
    ]

    operations = [
        RunPython(set_default_payment_status),
    ]
