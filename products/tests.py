
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product
from .views import (
    PRODUCT_DETAIL_CACHE_KEY,
    PRODUCT_LIST_CACHE_KEY,
)


User = get_user_model()


class ProductAPITest(APITestCase):

    def setUp(self):
        cache.clear()

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

        self.assertEqual(
            len(response.data),
            1,
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

    def test_product_list_is_cached(self):
        response = self.client.get(
            "/api/products/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        cached_products = cache.get(
            PRODUCT_LIST_CACHE_KEY
        )

        self.assertIsNotNone(
            cached_products
        )

        self.assertEqual(
            cached_products,
            response.data,
        )

    def test_product_list_cache_hit_avoids_database_query(self):
        cached_products = [
            {
                "id": self.product.id,
                "name": self.product.name,
                "description": self.product.description,
                "price": "1000.00",
                "stock": 10,
                "category": self.category.id,
                "created_at": self.product.created_at.isoformat().replace(
                    "+00:00",
                    "Z",
                ),
            }
        ]

        cache.set(
            PRODUCT_LIST_CACHE_KEY,
            cached_products,
        )

        with self.assertNumQueries(0):
            response = self.client.get(
                "/api/products/"
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data,
            cached_products,
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

        self.assertTrue(
            Product.objects.filter(
                name="Keyboard"
            ).exists()
        )

    def test_create_product_invalidates_product_list_cache(self):
        cache.set(
            PRODUCT_LIST_CACHE_KEY,
            [{"id": 999}],
        )

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

        self.assertIsNone(
            cache.get(PRODUCT_LIST_CACHE_KEY)
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

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.price,
            Decimal("1200.00"),
        )

    def test_update_product_invalidates_product_caches(self):
        cache.set(
            PRODUCT_LIST_CACHE_KEY,
            [{"id": self.product.id}],
        )

        cache.set(
            PRODUCT_DETAIL_CACHE_KEY.format(
                self.product.id
            ),
            {
                "id": self.product.id,
            },
        )

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

        self.assertIsNone(
            cache.get(PRODUCT_LIST_CACHE_KEY)
        )

        self.assertIsNone(
            cache.get(
                PRODUCT_DETAIL_CACHE_KEY.format(
                    self.product.id
                )
            )
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

        self.assertFalse(
            Product.objects.filter(
                id=self.product.id
            ).exists()
        )

    def test_delete_product_invalidates_product_caches(self):
        cache.set(
            PRODUCT_LIST_CACHE_KEY,
            [{"id": self.product.id}],
        )

        cache.set(
            PRODUCT_DETAIL_CACHE_KEY.format(
                self.product.id
            ),
            {
                "id": self.product.id,
            },
        )

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

        self.assertIsNone(
            cache.get(PRODUCT_LIST_CACHE_KEY)
        )

        self.assertIsNone(
            cache.get(
                PRODUCT_DETAIL_CACHE_KEY.format(
                    self.product.id
                )
            )
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

    def test_product_detail_returns_product(self):
        response = self.client.get(
            f"/api/products/{self.product.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.product.id,
        )

        self.assertEqual(
            response.data["name"],
            "Laptop",
        )

    def test_product_detail_is_cached(self):
        response = self.client.get(
            f"/api/products/{self.product.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        cache_key = PRODUCT_DETAIL_CACHE_KEY.format(
            self.product.id
        )

        cached_product = cache.get(
            cache_key
        )

        self.assertIsNotNone(
            cached_product
        )

        self.assertEqual(
            cached_product,
            response.data,
        )

    def test_product_detail_cache_hit_avoids_database_query(self):
        cached_product = {
            "id": self.product.id,
            "name": self.product.name,
            "description": self.product.description,
            "price": "1000.00",
            "stock": 10,
            "category": self.category.id,
            "created_at": self.product.created_at.isoformat().replace(
                "+00:00",
                "Z",
            ),
        }

        cache.set(
            PRODUCT_DETAIL_CACHE_KEY.format(
                self.product.id
            ),
            cached_product,
        )

        with self.assertNumQueries(0):
            response = self.client.get(
                f"/api/products/{self.product.id}/"
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data,
            cached_product,
        )

    def test_product_detail_returns_404_for_nonexistent_product(self):
        response = self.client.get(
            "/api/products/99999/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_product_cannot_use_nonexistent_category(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.post(
            "/api/products/",
            {
                "name": "Invalid Product",
                "description": "Invalid category",
                "price": "100.00",
                "stock": 10,
                "category": 99999,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Product.objects.filter(
                name="Invalid Product"
            ).exists()
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

        product = Product.objects.get(
            name="Out of Stock Product"
        )

        self.assertEqual(
            product.stock,
            0,
        )

    def test_staff_user_can_patch_stock(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.patch(
            f"/api/products/{self.product.id}/",
            {
                "stock": 25,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            25,
        )

    def test_staff_user_cannot_update_product_with_negative_price(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.patch(
            f"/api/products/{self.product.id}/",
            {
                "price": "-50.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.price,
            Decimal("1000.00"),
        )

    def test_staff_user_cannot_update_product_with_negative_stock(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.patch(
            f"/api/products/{self.product.id}/",
            {
                "stock": -5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )

    def test_product_detail_does_not_allow_post(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.post(
            f"/api/products/{self.product.id}/",
            {
                "name": "Invalid Method",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_product_list_does_not_allow_delete(self):
        self.client.force_authenticate(
            user=self.staff_user
        )

        response = self.client.delete(
            "/api/products/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
