from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product


User = get_user_model()


class ProductAPITest(APITestCase):

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff",
            password="testpass123",
            is_staff=True,
        )

        self.normal_user = User.objects.create_user(
            username="normal",
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

    def test_anonymous_user_can_list_products(self):
        response = self.client.get(
            "/api/products/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_normal_user_can_list_products(self):
        self.client.force_authenticate(
            user=self.normal_user
        )

        response = self.client.get(
            "/api/products/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_staff_user_can_create_product(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.post(
            "/api/products/",
            {
                "name": "Keyboard",
                "description": "Mechanical keyboard",
                "price": "150.00",
                "stock": 20,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_normal_user_cannot_create_product(self):
        self.client.force_authenticate(
            user=self.normal_user
        )

        response = self.client.post(
            "/api/products/",
            {
                "name": "Keyboard",
                "description": "Mechanical keyboard",
                "price": "150.00",
                "stock": 20,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_user_cannot_create_product(self):
        response = self.client.post(
            "/api/products/",
            {
                "name": "Keyboard",
                "description": "Mechanical keyboard",
                "price": "150.00",
                "stock": 20,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_staff_user_can_update_product(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.patch(
            f"/api/products/{self.product.id}/",
            {
                "price": "1200.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_normal_user_cannot_update_product(self):
        self.client.force_authenticate(
            user=self.normal_user
        )

        response = self.client.patch(
            f"/api/products/{self.product.id}/",
            {
                "price": "1200.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_user_can_delete_product(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.delete(
            f"/api/products/{self.product.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_normal_user_cannot_delete_product(self):
        self.client.force_authenticate(
            user=self.normal_user
        )

        response = self.client.delete(
            f"/api/products/{self.product.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_product_cannot_have_negative_price(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.post(
            "/api/products/",
            {
                "name": "Invalid Product",
                "description": "Invalid price",
                "price": "-100.00",
                "stock": 10,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_product_cannot_have_zero_price(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.post(
            "/api/products/",
            {
                "name": "Invalid Product",
                "description": "Zero price",
                "price": "0.00",
                "stock": 10,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_product_cannot_have_negative_stock(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.post(
            "/api/products/",
            {
                "name": "Invalid Product",
                "description": "Invalid stock",
                "price": "100.00",
                "stock": -5,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_product_can_have_zero_stock(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.post(
            "/api/products/",
            {
                "name": "Out of Stock Product",
                "description": "Valid zero stock",
                "price": "100.00",
                "stock": 0,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )