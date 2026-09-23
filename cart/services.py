from django.db import transaction

from .models import Cart, CartItem


@transaction.atomic
def add_to_cart(user, product, quantity):
    cart, _ = Cart.objects.get_or_create(user=user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity},
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save(update_fields=["quantity"])

    return cart_item