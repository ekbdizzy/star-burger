from collections import defaultdict
from operator import itemgetter

from django import forms
from django.conf import settings
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from geopy import distance

from address.models import Address
from address.services import fetch_coordinates
from foodcartapp.models import Product, Restaurant, Order, OrderItem, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:
        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def get_restaurants(menu_items: list) -> defaultdict[tuple, set]:
    """Get restaurants where all of menu_items can be cooked.
    :return: tuple(name, address) in a key and set of product_ids in value."""
    restaurants = defaultdict(set)
    for menu_item in menu_items:
        restaurant_name, address, product_id, lon, lat = menu_item.values()
        restaurants[(restaurant_name, address, (lon, lat))].add(product_id)
    return restaurants


def filter_restaurants_by_products(
    restaurants: dict[tuple, set],
    products: set[int]
) -> list[tuple]:
    """Return list of restaurants where products can be cooked."""
    order_rests = []
    for restaurant, rest_products in restaurants.items():
        if products.issubset(rest_products):
            order_rests.append(restaurant)
    return order_rests


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


def add_distance_to_order(order, restaurants: list[tuple]) -> list[tuple]:

    order_coords = (order.coord_lon, order.coord_lat)
    order_coords = (order_coords
                    if all(order_coords)
                    else get_or_fetch_coordinates(order.address))
    restaurants_with_distance = []
    for rest_name, rest_address, rest_coords in restaurants:
        rest_coords = (rest_coords
                       if all(rest_coords)
                       else get_or_fetch_coordinates(rest_address))
        if rest_coords:
            restaurants_with_distance.append(
                (rest_name, round(distance.distance(rest_coords, order_coords).km, 2)))
    return sorted(restaurants_with_distance, key=itemgetter(1))


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    excluded_statuses = ["5", "6"]

    orders = (Order.objects
              .prefetch_related('order_items', 'restaurant')
              .exclude(status__in=excluded_statuses)
              .get_order_price()
              .get_coordinates()
              .order_by('status')
              )
    order_items = OrderItem.objects.get_orders_items(orders)
    menu_items = RestaurantMenuItem.objects.get_matched_with_order_items(order_items)
    restaurants = get_restaurants(menu_items)

    for order in orders:
        order.product_ids = {product.product_id for product in order.order_items.all()}
        order.restaurants = filter_restaurants_by_products(
            restaurants, order.product_ids
        )
        order.restaurants = add_distance_to_order(order, order.restaurants)

    return render(request, template_name='order_items.html', context={
        "orders": orders
    })
