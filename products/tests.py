from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product


User = get_user_model()


class ProductAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        self.staff_user = User.objects.create_user(
            username="staffuser",
            password="testpassword123",
            is_staff=True,
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

    def test_anonymous_user_can_view_products(self):
        response = self.client.get(
            "/api/products/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_anonymous_user_can_view_product_detail(self):
        response = self.client.get(
            f"/api/products/{self.product.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_anonymous_user_cannot_create_product(self):
        response = self.client.post(
            "/api/products/",
            {
                "name": "Mouse",
                "description": "Gaming mouse",
                "price": "50.00",
                "stock": 20,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_normal_user_cannot_create_product(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            "/api/products/",
            {
                "name": "Mouse",
                "description": "Gaming mouse",
                "price": "50.00",
                "stock": 20,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_user_can_create_product(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.post(
            "/api/products/",
            {
                "name": "Mouse",
                "description": "Gaming mouse",
                "price": "50.00",
                "stock": 20,
                "category": self.category.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_normal_user_cannot_update_product(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.patch(
            f"/api/products/{self.product.id}/",
            {
                "price": "900.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_user_can_update_product(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.patch(
            f"/api/products/{self.product.id}/",
            {
                "price": "900.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            str(self.product.price),
            "900.00",
        )

    def test_normal_user_cannot_delete_product(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.delete(
            f"/api/products/{self.product.id}/"
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

        self.assertFalse(
            Product.objects.filter(
                id=self.product.id
            ).exists()
        )

    def test_normal_user_can_view_products(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/products/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )