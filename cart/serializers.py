from rest_framework import serializers

from products.models import Product
from .models import CartItem


class CartItemCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    quantity = serializers.IntegerField(min_value=1)


class CartItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "quantity",
        ]


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)