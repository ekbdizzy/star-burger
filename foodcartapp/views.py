from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response

from .models import Product, Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer


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
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    order = Order.objects.create(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address'],
    )

    products_fields = serializer.validated_data['products']
    products = [OrderItem(order=order, **fields) for fields in products_fields]
    OrderItem.objects.bulk_create(products)

    serializer = OrderSerializer(order)
    products = order.products.all()
    products_serializer = OrderItemSerializer(products, many=True)
    serializer.products = products_serializer

    mock_request = {
        "products": [{"product": 1, "quantity": 1}],
        "firstname": "Aleshka",
        "lastname": "Петров",
        "phonenumber": "+79291000000",
        "address": "Москва"
    }
    return Response(serializer.data, status=status.HTTP_201_CREATED)
