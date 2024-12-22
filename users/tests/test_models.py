from django.test import TestCase
from django.core.exceptions import ValidationError
from users.models import Profile, User


class UserModelTest(TestCase):
    def test_create_user_with_valid_email(self):
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("password123"))

    def test_create_user_with_invalid_email(self):
        user = User(username="testuser", email="invalid-email")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_user_str(self):
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.assertEqual(str(user), "User: testuser")


class ProfileModelTest(TestCase):
    def test_create_profile(self):
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        profile = Profile.objects.create(
            user=user, bio="This is a bio", avatar="http://example.com/avatar.jpg"
        )
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.bio, "This is a bio")
        self.assertEqual(profile.avatar, "http://example.com/avatar.jpg")

    def test_profile_str(self):
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        profile = Profile.objects.create(
            user=user, bio="This is a bio", avatar="http://example.com/avatar.jpg"
        )
        self.assertEqual(str(profile), "testuser's profile")
