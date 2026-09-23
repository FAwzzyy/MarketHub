from django.urls import path

from .views import (
    create_order,
    order_detail,
    order_list,
)


urlpatterns = [
    path(
        "orders/",
        order_list,
        name="order-list",
    ),
    path(
        "orders/create/",
        create_order,
        name="order-create",
    ),
    path(
        "orders/<int:order_id>/",
        order_detail,
        name="order-detail",
    ),
]