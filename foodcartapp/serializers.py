from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'address', 'firstname', 'lastname', 'phonenumber', 'products', 'comment']

    products = OrderItemSerializer(many=True)
    comment = serializers.CharField(read_only=True)
