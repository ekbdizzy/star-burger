from django.db import models
from django.db.models import Q


class AddressQueryset(models.QuerySet):
    def get_addresses_from_db(self, orders, restaurants):
        query = self.filter(
            Q(address__in=[order.address for order in orders]) |
            Q(address__in=[rest[1] for rest in restaurants])
        )
        return query


class Address(models.Model):
    address = models.CharField('Адрес', max_length=200, unique=True, db_index=True)
    latitude = models.FloatField('Координаты широты')
    longitude = models.FloatField('Координаты долготы')

    objects = AddressQueryset.as_manager()

    def get_coordinates(self) -> tuple[float, float]:
        return self.longitude, self.latitude

    def __str__(self):
        return self.address

    class Meta:
        verbose_name = 'Адрес с координатами'
        verbose_name_plural = 'Адреса с координатами'
