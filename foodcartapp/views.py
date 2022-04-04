import json

from django.http import JsonResponse
from django.templatetags.static import static

from .models import Product, Order, OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def register_order(request):
    response = request.body

    # mock_order = {"products": [{"product": 4, "quantity": 1}, {"product": 2, "quantity": 2}],
    #               "firstname": "Aleksey",
    #               "lastname": "Koshkin",
    #               "phonenumber": "89857243204",
    #               "address": "Москва, Цветной бульвар, 11с2"
    #               }

    if request.method == 'POST':
        order_details = json.loads(request.body)

        order = Order.objects.create(
            firstname=order_details['firstname'],
            lastname=order_details['lastname'],
            phone_number=order_details['phonenumber'],
            address=order_details['address']
        )

        order_items = order_details.get('products')
        for item in order_items:
            OrderItem.objects.create(
                order=order,
                product=Product.objects.get(id=item['product']),
                quantity=item.get('quantity')
            )

        return JsonResponse({})
