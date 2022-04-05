import json

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from phonenumbers import is_valid_number, parse

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


@api_view(['POST'])
@permission_classes([AllowAny, ])
def register_order(request):
    order_details = request.data
    order_products = order_details.get('products', '')
    firstname = order_details.get('firstname')
    lastname = order_details.get('lastname')
    phone_number = order_details.get('phonenumber')
    address = order_details.get('address')

    if isinstance(order_products, str):
        return Response({'products': 'Ожидался list со значениями, но был получен "str"'},
                        status=status.HTTP_400_BAD_REQUEST)

    if order_products is None:
        return Response({'products': 'Это поле не может быть пустым.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if order_products == []:
        return Response({'products': 'Этот список не может быть пустым.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if order_products == '':
        return Response({'products': 'Обязательное поле.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if not phone_number:
        return Response({'phone_number': 'Это поле не может быть пустым.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if firstname is None:
        return Response({'firstname': 'Это поле не может быть пустым.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(firstname, str):
        return Response({'firstname': 'Это поле должно быть строкой.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if not is_valid_number(parse(phone_number, 'RU')):
        return Response({'phonenumber': 'Введен некорректный номер телефона.'},
                        status=status.HTTP_400_BAD_REQUEST)

    order = Order.objects.create(
        firstname=firstname,
        lastname=lastname,
        phone_number=phone_number,
        address=address,
    )

    for product in order_products:
        try:
            order_product = Product.objects.get(id=product['product'])
        except Product.DoesNotExist:
            return Response({'products': f'Недопустимый первичный ключ {product["product"]}'})

        OrderItem.objects.create(
            order=order,
            product=order_product,
            quantity=product.get('quantity')
        )

    return JsonResponse({})
