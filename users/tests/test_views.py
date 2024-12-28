from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_register_user(self):
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User registered successfully")

    def test_register_user_existing_username(self):
        url = reverse("register")
        data = {
            "username": "testuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Username already exists")

    def test_register_user_existing_email(self):
        url = reverse("register")
        data = {
            "username": "testuser2",
            "email": "test@example.com",
            "password": "newpassword123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Email already exists")

    def test_user_profile_get(self):
        url = reverse("user_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_user_profile_put(self):
        url = reverse("user_profile")
        data = {"profile": {"bio": "Updated bio"}}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bio"], "Updated bio")

    def test_change_password(self):
        url = reverse("change_password")
        data = {
            "old_password": "password123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password updated successfully")

    def test_change_password_incorrect_old_password(self):
        url = reverse("change_password")
        data = {
            "old_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Old password is incorrect")

    def test_change_password_mismatch(self):
        url = reverse("change_password")
        data = {
            "old_password": "password123",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "New passwords do not match")

    # @patch('users.views.send_mail')
    # def test_forgot_password(self, mock_send_mail):
    #     url = reverse('forgot_password')
    #     data = {
    #         "email": "testuser@example.com"
    #     }
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data["message"], "Password reset email sent")
    #     mock_send_mail.assert_called_once()

    def test_forgot_password_no_user(self):
        url = reverse("forgot_password")
        data = {"email": "nouser@example.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "No user with this email exists")
