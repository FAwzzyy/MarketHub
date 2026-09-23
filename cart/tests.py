from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Cart, CartItem
from products.models import Category, Product


User = get_user_model()


class CartAPITest(APITestCase):

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
            price=1000.00,
            stock=10,
            category=self.category,
        )

        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_can_add_product_to_cart(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            CartItem.objects.count(),
            1
        )

        cart_item = CartItem.objects.first()

        self.assertEqual(
            cart_item.quantity,
            2
        )

        self.assertEqual(
            cart_item.product,
            self.product
        )

    def test_adding_same_product_increases_quantity(self):
        self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 3,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            CartItem.objects.count(),
            1
        )

        cart_item = CartItem.objects.first()

        self.assertEqual(
            cart_item.quantity,
            5
        )

    def test_unauthenticated_user_cannot_add_product_to_cart(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.assertEqual(
            CartItem.objects.count(),
            0
        )

    def test_quantity_zero_is_rejected(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 0,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            CartItem.objects.count(),
            0
        )

    def test_invalid_product_is_rejected(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": 99999,
                "quantity": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            CartItem.objects.count(),
            0
        )

    def test_authenticated_user_can_view_cart(self):
        self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        response = self.client.get(
            "/api/cart/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            len(response.data["items"]),
            1
        )

        self.assertEqual(
            response.data["items"][0]["product"],
            self.product.id
        )

        self.assertEqual(
            response.data["items"][0]["quantity"],
            2
        )

    def test_authenticated_user_can_update_cart_item_quantity(self):
        self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        cart_item = CartItem.objects.first()

        response = self.client.patch(
            f"/api/cart/items/{cart_item.id}/",
            {
                "quantity": 5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["quantity"],
            5
        )

        cart_item.refresh_from_db()

        self.assertEqual(
            cart_item.quantity,
            5
        )

    def test_update_quantity_zero_is_rejected(self):
        self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        cart_item = CartItem.objects.first()

        response = self.client.patch(
            f"/api/cart/items/{cart_item.id}/",
            {
                "quantity": 0,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        cart_item.refresh_from_db()

        self.assertEqual(
            cart_item.quantity,
            2
        )

    def test_user_cannot_update_another_users_cart_item(self):
        other_cart = Cart.objects.create(
            user=self.other_user
        )

        other_cart_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=2,
        )

        response = self.client.patch(
            f"/api/cart/items/{other_cart_item.id}/",
            {
                "quantity": 5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        other_cart_item.refresh_from_db()

        self.assertEqual(
            other_cart_item.quantity,
            2
        )

    def test_authenticated_user_can_delete_cart_item(self):
        self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        cart_item = CartItem.objects.first()

        response = self.client.delete(
            f"/api/cart/items/{cart_item.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertEqual(
            CartItem.objects.count(),
            0
        )

    def test_user_cannot_delete_another_users_cart_item(self):
        other_cart = Cart.objects.create(
            user=self.other_user
        )

        other_cart_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=2,
        )

        response = self.client.delete(
            f"/api/cart/items/{other_cart_item.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.assertTrue(
            CartItem.objects.filter(
                id=other_cart_item.id
            ).exists()
        )