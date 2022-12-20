# Generated by Django 3.2 on 2022-06-07 14:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0058_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, max_length=500, verbose_name='Комментарий'),
        ),
        migrations.AlterField(
            model_name='order',
            name='restaurant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='foodcartapp.restaurant', verbose_name='Какой ресторан готовит'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='foodcartapp.order', verbose_name='Заказ'),
        ),
    ]