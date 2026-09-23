from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from cart.models import Cart
from .models import Order, OrderItem


@transaction.atomic
def create_order_from_cart(user):
    try:
        cart = Cart.objects.prefetch_related(
            "items__product"
        ).get(user=user)
    except Cart.DoesNotExist:
        raise ValidationError(
            {"detail": "Cart is empty."}
        )

    cart_items = list(cart.items.all())

    if not cart_items:
        raise ValidationError(
            {"detail": "Cart is empty."}
        )

    for cart_item in cart_items:
        if cart_item.product.stock < cart_item.quantity:
            raise ValidationError(
                {
                    "detail": (
                        f"Not enough stock for "
                        f"{cart_item.product.name}."
                    )
                }
            )

    total_amount = Decimal("0.00")

    order = Order.objects.create(
        user=user,
        status=Order.Status.CONFIRMED,
        total_amount=Decimal("0.00"),
    )

    for cart_item in cart_items:
        product = cart_item.product

        unit_price = product.price

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=cart_item.quantity,
            unit_price=unit_price,
        )

        total_amount += unit_price * cart_item.quantity

        product.stock -= cart_item.quantity
        product.save(update_fields=["stock"])

    order.total_amount = total_amount
    order.save(update_fields=["total_amount"])

    cart.items.all().delete()

    return order