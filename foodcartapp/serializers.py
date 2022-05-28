from rest_framework.serializers import ModelSerializer

from .models import Order, OrderItem


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'address', 'firstname', 'lastname', 'phonenumber', 'products']

    products = OrderItemSerializer(many=True)
