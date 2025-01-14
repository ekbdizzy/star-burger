from collections import defaultdict

from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from address.models import Address
from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from foodcartapp.order_tools import filter_by_product_and_add_distance


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


def get_restaurants_with_available_products(menu_items: list) -> defaultdict[tuple, set]:
    """Get restaurants where all of menu_items can be cooked.
    :return: tuple(name, address) in a key and set of product_ids in value."""
    restaurants = defaultdict(set)
    for menu_item in menu_items:
        restaurant_name, address, product_id, lon, lat = menu_item.values()
        restaurants[(restaurant_name, address, (lon, lat))].add(product_id)
    return restaurants


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    statuses = ["1", "2", "3", "4"]

    orders = (Order.objects
              .prefetch_related('items', 'restaurant')
              .filter(status__in=statuses)
              .get_order_price()
              .get_coordinates()
              .order_by('status')
              )
    order_items = orders.get_orders_items()
    menu_items = RestaurantMenuItem.objects.get_matched_with_order_items(order_items)
    restaurants = get_restaurants_with_available_products(menu_items)

    order_and_rest_addresses = {
        *[order.address for order in orders],
        *[address for _, address, _ in restaurants]
    }
    addresses = Address.objects.get_or_create_addresses_with_coord(order_and_rest_addresses)

    for order in orders:
        order.restaurants = filter_by_product_and_add_distance(order, restaurants, addresses)

    return render(request, template_name='order_items.html', context={
        "orders": orders
    })
