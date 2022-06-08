from django.db import models
from django.db.models import Sum, F, OuterRef, Subquery
from django.core.validators import MinValueValidator

from phonenumber_field.modelfields import PhoneNumberField

from address.models import Address


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
                .filter(availability=True)
                .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50,
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50,
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=500,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItemQuerySet(models.QuerySet):
    def get_matched_with_order_items(self, order_items: dict):
        addresses = Address.objects.filter(address=OuterRef('restaurant__address'))
        return (self
                .select_related('restaurant', 'product')
                .filter(availability=True, product_id__in=order_items)
                .annotate(coord_lon=Subquery(addresses.values('longitude')),
                          coord_lat=Subquery(addresses.values('latitude')))
                .values('restaurant__name',
                        'restaurant__address',
                        'coord_lon',
                        'coord_lat',
                        'product_id', )
                )


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    objects = RestaurantMenuItemQuerySet.as_manager()

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQueryset(models.QuerySet):
    def get_order_price(self):
        return self.annotate(
            order_price=Sum(F('items__quantity') * F('items__product__price'))
        )

    def get_coordinates(self):
        addresses = Address.objects.filter(address=OuterRef('address'))
        return self.annotate(coord_lon=Subquery(addresses.values('longitude')),
                             coord_lat=Subquery(addresses.values('latitude')))

    def get_orders_items(self):
        return self.values_list('items__product_id').distinct()



class Order(models.Model):
    """Модель заказа."""

    NEW = '1'
    APPROVED = '2'
    COOKING = '3'
    DELIVERING = '4'
    COMPLETED = '5'
    CANCELLED = '6'

    STATUS_CHOICES = (
        (NEW, 'Необработан'),
        (APPROVED, 'Подтвержден'),
        (COOKING, 'Готовится'),
        (DELIVERING, 'Доставляется'),
        (COMPLETED, 'Завершен'),
        (CANCELLED, 'Отменен'),
    )

    PAYMENT_CHOICES = (
        ("cash", "наличными"),
        ("online", "электронно"),
    )

    address = models.CharField('Адрес', max_length=300)
    firstname = models.CharField('Имя покупателя', max_length=100)
    lastname = models.CharField('Фамилия покупателя', max_length=100, db_index=True)
    phonenumber = PhoneNumberField('Номер телефона', db_index=True)
    status = models.CharField(
        'Статус заказа',
        max_length=15,
        choices=STATUS_CHOICES,
        db_index=True,
        default='1',
    )
    payment_type = models.CharField(
        'Способ оплаты',
        choices=PAYMENT_CHOICES,
        max_length=10,
        db_index=True,
    )
    comment = models.TextField('Комментарий', max_length=500, blank=True)
    registered_at = models.DateTimeField('Когда создан', auto_now_add=True, db_index=True)
    called_at = models.DateTimeField('Когда подтвержден', db_index=True, blank=True, null=True)
    delivered_at = models.DateTimeField('Когда доставлен', db_index=True, blank=True, null=True)
    restaurant = models.ForeignKey(Restaurant,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True,
                                   related_name='orders',
                                   verbose_name='Какой ресторан готовит'
                                   )

    objects = OrderQueryset.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname} {self.address}'


class OrderItem(models.Model):
    """Модель продукта в заказе."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ', )
    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        related_name='order_items',
        verbose_name='Продукты в заказе',
    )
    price = models.DecimalField(
        "Цена",
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity = models.IntegerField('Количество', validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Продукт в заказе'
        verbose_name_plural = 'Продукты в заказе'
        ordering = ('product',)

    def __str__(self):
        return f'{self.product}: {self.order}'
