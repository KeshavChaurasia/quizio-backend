from django.test import SimpleTestCase
from django.urls import reverse, resolve
from rest_framework_simplejwt.views import TokenRefreshView
from users import views


class TestUrls(SimpleTestCase):
    def test_token_obtain_pair_url(self):
        url = reverse("token_obtain_pair")
        self.assertEqual(resolve(url).func.view_class, views.CustomTokenObtainPairView)

    def test_token_refresh_url(self):
        url = reverse("token_refresh")
        self.assertEqual(resolve(url).func.view_class, TokenRefreshView)

    def test_register_url(self):
        url = reverse("register")
        self.assertEqual(resolve(url).func, views.register_user)

    def test_user_profile_url(self):
        url = reverse("user_profile")
        self.assertEqual(resolve(url).func, views.user_profile)

    def test_change_password_url(self):
        url = reverse("change_password")
        self.assertEqual(resolve(url).func, views.change_password)

    def test_forgot_password_url(self):
        url = reverse("forgot_password")
        self.assertEqual(resolve(url).func, views.forgot_password)
