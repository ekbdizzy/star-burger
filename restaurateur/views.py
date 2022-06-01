from collections import defaultdict

from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

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


def filter_restaurants_by_products(
    restaurants: dict[str, set],
    products: set[int]
) -> list[str]:
    """Return list of restaurants names where products can be cooked."""
    order_rests = []
    for restaurant, rest_products in restaurants.items():
        if products.issubset(rest_products):
            order_rests.append(restaurant)
    return order_rests


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    excluded_statuses = ["COMPLETED", "CANCELLED"]
    orders = (Order.objects
              .prefetch_related('products')
              .exclude(status__in=excluded_statuses)
              .get_order_price())
    order_items = OrderItem.objects.get_orders_items(orders)
    menu_items = RestaurantMenuItem.objects.get_matched_with_order_items(order_items)

    restaurants = defaultdict(set)
    for menu_item in menu_items:
        restaurant, product_id = menu_item.values()
        restaurants[restaurant].add(product_id)

    for order in orders:
        order.product_ids = {product.product_id for product in order.products.all()}
        order.restaurants = filter_restaurants_by_products(
            restaurants, order.product_ids
        )

    return render(request, template_name='order_items.html', context={
        "orders": orders
    })

