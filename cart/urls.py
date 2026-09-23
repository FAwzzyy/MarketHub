from django.urls import path

from .views import (
    add_cart_item,
    cart_item_detail,
    get_cart,
)


urlpatterns = [
    path(
        "cart/items/",
        add_cart_item,
        name="cart-add-item",
    ),
    path(
        "cart/",
        get_cart,
        name="cart-detail",
    ),
    path(
        "cart/items/<int:item_id>/",
        cart_item_detail,
        name="cart-item-detail",
    ),
]