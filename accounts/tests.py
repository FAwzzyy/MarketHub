from django.contrib.auth import get_user_model
from django.test import Client

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
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            User.objects.filter(username="newuser").exists()
        )

    def test_registered_password_is_hashed(self):
        self.client.post(
            "/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )

        user = User.objects.get(username="newuser")

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
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            User.objects.filter(username="existinguser").count(),
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

        self.assertEqual(response.status_code, 200)

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

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Invalid username or password",
        )

    def test_authenticated_user_can_access_profile(self):
        user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.client.login(
            username="testuser",
            password="testpass123",
        )

        response = self.client.get("/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "testuser",
        )

    def test_unauthenticated_user_cannot_access_profile(self):
        response = self.client.get("/profile/")

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_user_can_logout(self):
        User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.client.login(
            username="testuser",
            password="testpass123",
        )

        response = self.client.get("/logout/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Logout successful!",
        )

    def test_user_can_obtain_jwt_token(self):
        User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        response = self.client.post(
            "/api/auth/token/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_user_can_refresh_jwt_token(self):
        User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        token_response = self.client.post(
            "/api/auth/token/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )

        refresh_token = token_response.data["refresh"]

        response = self.client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": refresh_token,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

    def test_login_requires_csrf_token(self):
        client = Client(
            enforce_csrf_checks=True
        )

        response = client.post(
            "/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_register_requires_csrf_token(self):
        client = Client(
            enforce_csrf_checks=True
        )

        response = client.post(
            "/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )