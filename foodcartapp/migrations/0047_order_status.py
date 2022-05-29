# Generated by Django 3.2 on 2022-05-29 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_alter_orderitem_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Необработан', 'Необработан'), ('Подтвержден', 'Подтвержден'), ('Готовится', 'Готовится'), ('Доставляется', 'Доставляется'), ('Завершен', 'Завершен'), ('Отменен', 'Отменен')], db_index=True, default='Необработан', max_length=15, verbose_name='Статус заказа'),
        ),
    ]
