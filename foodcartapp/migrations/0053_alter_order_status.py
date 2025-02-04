# Generated by Django 3.2 on 2022-05-31 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0052_alter_order_payment_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('NEW', 'Необработан'), ('APPROVED', 'Подтвержден'), ('COOKING', 'Готовится'), ('DELIVERING', 'Доставляется'), ('COMPLETED', 'Завершен'), ('CANCELLED', 'Отменен')], db_index=True, default='Необработан', max_length=15, verbose_name='Статус заказа'),
        ),
    ]
