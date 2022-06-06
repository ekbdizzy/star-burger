import requests
from django.conf import settings

from .models import Address


def fetch_coordinates(apikey: str, address: str) -> tuple[int, int] | None:
    """Fetch coordinates of address."""
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_or_fetch_coordinates(address: str) -> tuple[float, float] | None:
    """Try to get coordinates form Address model.
    If there is no address, try to fetch it from Yandex Geocoder and save to DB.
    :return: longitude, latitude.
    If fetch is failed return None."""

    try:
        obj = Address.objects.get(address=address)
        return obj.longitude, obj.latitude
    except Address.DoesNotExist:
        coords = fetch_coordinates(settings.YANDEX_API_KEY, address)
        if not coords:
            return
        longitude, latitude = coords
        Address.objects.create(address=address, latitude=latitude, longitude=longitude)
        return longitude, latitude
