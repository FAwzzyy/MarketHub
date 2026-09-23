from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import (
    CartItemCreateSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
)
from .services import add_to_cart


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_cart_item(request):
    serializer = CartItemCreateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    cart_item = add_to_cart(
        user=request.user,
        product=serializer.validated_data["product"],
        quantity=serializer.validated_data["quantity"],
    )

    return Response(
        {
            "id": cart_item.id,
            "product": cart_item.product_id,
            "quantity": cart_item.quantity,
        },
        status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart, _ = Cart.objects.get_or_create(
        user=request.user
    )

    serializer = CartItemSerializer(
        cart.items.all(),
        many=True
    )

    return Response(
        {
            "items": serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def cart_item_detail(request, item_id):
    try:
        cart_item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )

    except CartItem.DoesNotExist:
        return Response(
            {"detail": "Cart item not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "PATCH":
        serializer = CartItemUpdateSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = serializer.validated_data["quantity"]
        cart_item.save(update_fields=["quantity"])

        return Response(
            {
                "id": cart_item.id,
                "product": cart_item.product_id,
                "quantity": cart_item.quantity,
            },
            status=status.HTTP_200_OK
        )

    elif request.method == "DELETE":
        cart_item.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )