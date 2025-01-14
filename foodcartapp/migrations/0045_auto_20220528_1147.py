# Generated by Django 3.2 on 2022-05-28 11:47

from django.db import migrations
from django.db.migrations import RunPython


def set_order_item_price(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    order_items = OrderItem.objects.select_related('product').all()
    order_items_iter = order_items.iterator()
    for item in order_items_iter:
        item.price = item.product.price
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0044_orderitem_price'),
    ]

    operations = [
        RunPython(set_order_item_price)
    ]
