# Generated by Django 3.2 on 2022-05-30 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0049_auto_20220530_1231'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_type',
            field=models.CharField(choices=[('cash', 'наличными'), ('online', 'электронно')], db_index=True, default='cash', max_length=10, verbose_name='Способ оплаты'),
        ),
    ]