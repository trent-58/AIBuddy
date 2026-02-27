from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class MatchingTests(APITestCase):
    def setUp(self):
        self.password = "StrongPass123"
        self.user = User.objects.create_user(
            username="solo_user",
            password=self.password,
            interests=["go"],
        )

    def test_find_returns_solo_when_no_partner(self):
        login = self.client.post(
            "/user/login/",
            {"username": "solo_user", "password": self.password},
            format="json",
        )
        token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get("/matching/find/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_solo"])
        self.assertIsNone(response.data["matched_user_id"])
