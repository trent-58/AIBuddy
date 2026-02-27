from rest_framework import status
from rest_framework.test import APITestCase


class AuthTests(APITestCase):
    def test_register_and_login(self):
        register = self.client.post(
            "/user/register/",
            {
                "username": "new_user",
                "password": "StrongPass123",
                "interests": ["ml", "python"],
                "bio": "Learner",
            },
            format="json",
        )
        self.assertEqual(register.status_code, status.HTTP_201_CREATED)

        login = self.client.post(
            "/user/login/",
            {"username": "new_user", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access", login.data)
