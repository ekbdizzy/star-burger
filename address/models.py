from django.db import models


class Address(models.Model):
    address = models.CharField('Адрес', max_length=200, unique=True, db_index=True)
    latitude = models.FloatField('Координаты широты', null=True, blank=True)
    longitude = models.FloatField('Координаты долготы', null=True, blank=True)

    def __str__(self):
        return self.address

    class Meta:
        verbose_name = 'Адрес с координатами'
        verbose_name_plural = 'Адреса с координатами'
