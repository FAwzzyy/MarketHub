from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order
from .serializers import OrderSerializer
from .services import create_order_from_cart


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):

    order = create_order_from_cart(
        user=request.user
    )

    serializer = OrderSerializer(order)

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_list(request):

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    serializer = OrderSerializer(
        orders,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):

    try:
        order = (
            Order.objects
            .prefetch_related("items__product")
            .get(
                id=order_id,
                user=request.user,
            )
        )

    except Order.DoesNotExist:
        return Response(
            {"detail": "Order not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = OrderSerializer(order)

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )