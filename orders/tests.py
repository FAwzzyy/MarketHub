from decimal import Decimal

from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from products.models import Category, Product

from .models import Order, OrderItem


User = get_user_model()


class OrderAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            password="testpassword123",
        )

        self.category = Category.objects.create(
            name="Electronics"
        )

        self.product = Product.objects.create(
            name="Laptop",
            description="Test laptop",
            price="1000.00",
            stock=10,
            category=self.category,
        )

        self.keyboard = Product.objects.create(
            name="Keyboard",
            description="Test keyboard",
            price="100.00",
            stock=20,
            category=self.category,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def add_to_cart(
        self,
        product,
        quantity,
    ):
        cart, _ = Cart.objects.get_or_create(
            user=self.user
        )

        return CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
        )

    def test_user_can_create_order_from_cart(self):
        self.add_to_cart(
            self.product,
            2,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Order.objects.count(),
            1,
        )

        order = Order.objects.first()

        self.assertEqual(
            order.user,
            self.user,
        )

        self.assertEqual(
            order.total_amount,
            Decimal("2000.00"),
        )

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

        self.assertEqual(
            response.data["id"],
            order.id,
        )

    def test_order_contains_correct_order_item(self):
        self.add_to_cart(
            self.product,
            2,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.first()
        order_item = OrderItem.objects.get(
            order=order
        )

        self.assertEqual(
            order_item.product,
            self.product,
        )

        self.assertEqual(
            order_item.quantity,
            2,
        )

        self.assertEqual(
            order_item.unit_price,
            Decimal("1000.00"),
        )

    def test_order_item_keeps_original_product_price(self):
        self.add_to_cart(
            self.product,
            1,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.product.price = "1500.00"
        self.product.save()

        order_item = OrderItem.objects.first()

        self.assertEqual(
            order_item.unit_price,
            Decimal("1000.00"),
        )

    def test_stock_is_decreased_after_order(self):
        self.add_to_cart(
            self.product,
            3,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            7,
        )

    def test_multiple_products_are_included_in_order(self):
        self.add_to_cart(
            self.product,
            2,
        )

        self.add_to_cart(
            self.keyboard,
            3,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.first()

        self.assertEqual(
            order.items.count(),
            2,
        )

        self.assertEqual(
            order.total_amount,
            Decimal("2300.00"),
        )

        laptop_item = order.items.get(
            product=self.product
        )

        keyboard_item = order.items.get(
            product=self.keyboard
        )

        self.assertEqual(
            laptop_item.quantity,
            2,
        )

        self.assertEqual(
            keyboard_item.quantity,
            3,
        )

    def test_cart_is_cleared_after_order(self):
        self.add_to_cart(
            self.product,
            2,
        )

        self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        cart = Cart.objects.get(
            user=self.user
        )

        self.assertEqual(
            cart.items.count(),
            0,
        )

    def test_empty_cart_cannot_create_order(self):
        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

    def test_cart_with_no_items_cannot_create_order(self):
        Cart.objects.create(
            user=self.user
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

    def test_insufficient_stock_is_rejected(self):
        self.add_to_cart(
            self.product,
            11,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

        self.assertEqual(
            OrderItem.objects.count(),
            0,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )

    def test_stock_is_not_changed_when_any_product_has_insufficient_stock(self):
        self.add_to_cart(
            self.product,
            2,
        )

        self.add_to_cart(
            self.keyboard,
            21,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

        self.assertEqual(
            OrderItem.objects.count(),
            0,
        )

        self.product.refresh_from_db()
        self.keyboard.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )

        self.assertEqual(
            self.keyboard.stock,
            20,
        )

    def test_cart_is_not_cleared_when_order_creation_fails(self):
        self.add_to_cart(
            self.product,
            11,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        cart = Cart.objects.get(
            user=self.user
        )

        self.assertEqual(
            cart.items.count(),
            1,
        )

        cart_item = cart.items.first()

        self.assertEqual(
            cart_item.quantity,
            11,
        )

    def test_invalid_cart_quantity_is_rejected(self):
        self.add_to_cart(
            self.product,
            0,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )


    def test_unauthenticated_user_cannot_create_order(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

    def test_user_can_view_own_orders(self):
        self.add_to_cart(
            self.product,
            1,
        )

        create_response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.get(
            "/api/orders/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            create_response.data["id"],
        )

    def test_unauthenticated_user_cannot_view_orders(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            "/api/orders/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_can_view_own_order_detail(self):
        self.add_to_cart(
            self.product,
            1,
        )

        create_response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        order_id = create_response.data["id"]

        response = self.client.get(
            f"/api/orders/{order_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            order_id,
        )

        self.assertEqual(
            len(response.data["items"]),
            1,
        )

    def test_user_cannot_view_another_users_order(self):
        other_order = Order.objects.create(
            user=self.other_user,
            status=Order.Status.CONFIRMED,
            total_amount=Decimal("1000.00"),
        )

        response = self.client.get(
            f"/api/orders/{other_order.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unauthenticated_user_cannot_view_order_detail(self):
        self.add_to_cart(
            self.product,
            1,
        )

        create_response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        order_id = create_response.data["id"]

        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            f"/api/orders/{order_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_order_total_is_calculated_from_unit_price_and_quantity(self):
        self.add_to_cart(
            self.product,
            2,
        )

        self.add_to_cart(
            self.keyboard,
            4,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.first()

        expected_total = (
            Decimal("1000.00") * 2
            + Decimal("100.00") * 4
        )

        self.assertEqual(
            order.total_amount,
            expected_total,
        )

    def test_order_status_is_confirmed_after_creation(self):
        self.add_to_cart(
            self.product,
            1,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.first()

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

    def test_created_order_belongs_to_authenticated_user(self):
        self.add_to_cart(
            self.product,
            1,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.first()

        self.assertEqual(
            order.user,
            self.user,
        )

    def test_order_item_count_matches_cart_items(self):
        self.add_to_cart(
            self.product,
            2,
        )

        self.add_to_cart(
            self.keyboard,
            3,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.first()

        self.assertEqual(
            order.items.count(),
            2,
        )

        self.assertEqual(
            OrderItem.objects.count(),
            2,
        )