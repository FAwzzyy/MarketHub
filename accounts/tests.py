from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AccountsAPITest(APITestCase):

    def test_user_can_register(self):
        response = self.client.post(
            "/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "testpass123",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            User.objects.filter(
                username="newuser"
            ).exists()
        )

    def test_registered_password_is_hashed(self):
        self.client.post(
            "/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "testpass123",
            },
        )

        user = User.objects.get(
            username="newuser"
        )

        self.assertNotEqual(
            user.password,
            "testpass123",
        )

        self.assertTrue(
            user.check_password("testpass123")
        )

    def test_user_cannot_register_with_duplicate_username(self):
        User.objects.create_user(
            username="existinguser",
            password="testpass123",
        )

        response = self.client.post(
            "/register/",
            {
                "username": "existinguser",
                "email": "another@example.com",
                "password": "testpass123",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            User.objects.filter(
                username="existinguser"
            ).count(),
            1,
        )

    def test_user_can_login(self):
        User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        response = self.client.post(
            "/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_user_cannot_login_with_invalid_password(self):
        User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        response = self.client.post(
            "/login/",
            {
                "username": "testuser",
                "password": "wrongpassword",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

    def test_authenticated_user_can_view_profile(self):
        User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.assertTrue(
            self.client.login(
                username="testuser",
                password="testpass123",
            )
        )

        response = self.client.get(
            "/profile/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_unauthenticated_user_cannot_view_profile(self):
        response = self.client.get(
            "/profile/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_302_FOUND,
        )

    def test_user_can_logout(self):
        User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.assertTrue(
            self.client.login(
                username="testuser",
                password="testpass123",
            )
        )

        response = self.client.get(
            "/logout/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        response = self.client.get(
            "/profile/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_302_FOUND,
        )