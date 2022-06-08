from django.conf import settings
from django.db import models

from address.services import fetch_coordinates


class AddressQuerySet(models.QuerySet):

    def get_or_create_addresses_with_coord(self, order_and_rest_addresses: set) -> dict[str]:
        """Return existing and fetched addresses from DB with coordinates.
        If address is absent in DB, it's requested in Yandex.Geocoder and save to DB."""
        existing_addresses = (self.filter(address__in=order_and_rest_addresses)
                              .values_list('address', 'longitude', 'latitude'))

        addresses_with_coord = {address: (longitude, latitude)
                                for address, longitude, latitude
                                in existing_addresses}
        new_addresses = []
        for address in order_and_rest_addresses ^ set(addresses_with_coord):
            lon, lat = fetch_coordinates(settings.YANDEX_API_KEY, address)
            addresses_with_coord[address] = (lon, lat)
            new_addresses.append({
                'address': address,
                'longitude': lon,
                'latitude': lat,
            })

        Address.objects.bulk_create([Address(**fields) for fields in new_addresses])
        return addresses_with_coord


class Address(models.Model):
    address = models.CharField('Адрес', max_length=200, unique=True, db_index=True)
    latitude = models.FloatField('Координаты широты', null=True, blank=True)
    longitude = models.FloatField('Координаты долготы', null=True, blank=True)

    objects = AddressQuerySet.as_manager()

    def __str__(self):
        return self.address

    class Meta:
        verbose_name = 'Адрес с координатами'
        verbose_name_plural = 'Адреса с координатами'
