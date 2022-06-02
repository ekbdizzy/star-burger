from collections import defaultdict

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme

from restaurateur.views import filter_restaurants_by_products, get_restaurants
from .models import Product, Order, OrderItem
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, ]

    fields = (
        "address",
        "firstname",
        "lastname",
        "phonenumber",
        "status",
        "payment_type",
        'restaurant',
        "comment",
        "registered_at",
        "called_at",
        "delivered_at",
    )

    readonly_fields = ("registered_at",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter restaurants where food can be cooked."""
        if db_field.name == "restaurant":
            obj_id = request.resolver_match.kwargs.get('object_id', None)
            if obj_id is None:
                return super().formfield_for_foreignkey(db_field, request, **kwargs)

            order_qs = (Order.objects
                        .filter(pk=obj_id)
                        .prefetch_related('products')
                        )
            order_items = OrderItem.objects.get_orders_items(order_qs)
            menu_items = RestaurantMenuItem.objects.get_matched_with_order_items(order_items)
            restaurants = get_restaurants(menu_items)

            order = order_qs.first()
            order.product_ids = {product.product_id for product in order.products.all()}
            order.restaurants = filter_restaurants_by_products(restaurants, order.product_ids)
            restaurant_names = [restaurant[0] for restaurant in order.restaurants]
            restaurants = Restaurant.objects.filter(name__in=restaurant_names).values_list('id')

            kwargs["queryset"] = Restaurant.objects.filter(id__in=restaurants)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.status in ['1', '2'] and obj.restaurant:
            obj.status = '3'
        super().save_model(request, obj, form, change)

    def response_post_save_change(self, request, obj):
        response = super().response_post_save_change(request, obj)
        next_url = request.GET.get('next', '')
        if url_has_allowed_host_and_scheme(next_url, settings.ALLOWED_HOSTS):
            return HttpResponseRedirect(next_url)
        return response
