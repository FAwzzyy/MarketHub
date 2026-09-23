from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Category, Product

from .models import Cart, CartItem


User = get_user_model()


class CartAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="other",
            password="testpass123",
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

    def test_user_can_add_product_to_cart(self):
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
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["product"],
            self.product.id,
        )

        self.assertEqual(
            response.data["quantity"],
            2,
        )

        self.assertEqual(
            CartItem.objects.count(),
            1,
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
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["quantity"],
            5,
        )

        self.assertEqual(
            CartItem.objects.count(),
            1,
        )

    def test_different_products_create_different_cart_items(self):
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
                "product": self.keyboard.id,
                "quantity": 3,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            CartItem.objects.count(),
            2,
        )

    def test_cart_belongs_to_authenticated_user(self):
        self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        cart = Cart.objects.get(
            user=self.user
        )

        self.assertEqual(
            cart.user,
            self.user,
        )

    def test_cannot_add_zero_quantity(self):
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
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            CartItem.objects.count(),
            0,
        )

    def test_cannot_add_negative_quantity(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": -1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            CartItem.objects.count(),
            0,
        )

    def test_cannot_add_nonexistent_product(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": 99999,
                "quantity": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            CartItem.objects.count(),
            0,
        )

    def test_user_can_view_own_cart(self):
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
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["items"]),
            1,
        )

        self.assertEqual(
            response.data["items"][0]["product"],
            self.product.id,
        )

        self.assertEqual(
            response.data["items"][0]["quantity"],
            2,
        )

    def test_empty_cart_returns_empty_items(self):
        response = self.client.get(
            "/api/cart/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["items"],
            [],
        )

    def test_unauthenticated_user_cannot_view_cart(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            "/api/cart/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unauthenticated_user_cannot_add_to_cart(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertEqual(
            CartItem.objects.count(),
            0,
        )

    def test_user_can_update_cart_item_quantity(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        item_id = response.data["id"]

        response = self.client.patch(
            f"/api/cart/items/{item_id}/",
            {
                "quantity": 5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["quantity"],
            5,
        )

        cart_item = CartItem.objects.get(
            id=item_id
        )

        self.assertEqual(
            cart_item.quantity,
            5,
        )

    def test_cannot_update_cart_item_to_zero(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        item_id = response.data["id"]

        response = self.client.patch(
            f"/api/cart/items/{item_id}/",
            {
                "quantity": 0,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        cart_item = CartItem.objects.get(
            id=item_id
        )

        self.assertEqual(
            cart_item.quantity,
            2,
        )

    def test_cannot_update_cart_item_to_negative_quantity(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        item_id = response.data["id"]

        response = self.client.patch(
            f"/api/cart/items/{item_id}/",
            {
                "quantity": -5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        cart_item = CartItem.objects.get(
            id=item_id
        )

        self.assertEqual(
            cart_item.quantity,
            2,
        )

    def test_cannot_update_nonexistent_cart_item(self):
        response = self.client.patch(
            "/api/cart/items/99999/",
            {
                "quantity": 5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_cannot_access_other_users_cart_item(self):
        other_cart = Cart.objects.create(
            user=self.other_user
        )

        cart_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=2,
        )

        response = self.client.patch(
            f"/api/cart/items/{cart_item.id}/",
            {
                "quantity": 5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        cart_item.refresh_from_db()

        self.assertEqual(
            cart_item.quantity,
            2,
        )

    def test_user_cannot_delete_other_users_cart_item(self):
        other_cart = Cart.objects.create(
            user=self.other_user
        )

        cart_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=2,
        )

        response = self.client.delete(
            f"/api/cart/items/{cart_item.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            CartItem.objects.filter(
                id=cart_item.id
            ).exists()
        )

    def test_user_can_delete_cart_item(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        item_id = response.data["id"]

        response = self.client.delete(
            f"/api/cart/items/{item_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            CartItem.objects.filter(
                id=item_id
            ).exists()
        )

    def test_cannot_delete_nonexistent_cart_item(self):
        response = self.client.delete(
            "/api/cart/items/99999/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unauthenticated_user_cannot_update_cart_item(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        item_id = response.data["id"]

        self.client.force_authenticate(
            user=None
        )

        response = self.client.patch(
            f"/api/cart/items/{item_id}/",
            {
                "quantity": 5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unauthenticated_user_cannot_delete_cart_item(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        item_id = response.data["id"]

        self.client.force_authenticate(
            user=None
        )

        response = self.client.delete(
            f"/api/cart/items/{item_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )