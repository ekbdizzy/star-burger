from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id',
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'payment_type',
            'products',
            'order_items',
            'comment'
        ]

    order_items = OrderItemSerializer(many=True, read_only=True)
    products = OrderItemSerializer(many=True, write_only=True)
    comment = serializers.CharField(read_only=True)
