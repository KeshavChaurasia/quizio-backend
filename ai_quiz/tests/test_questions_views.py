from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import AsyncMock, patch
from ai_quiz.models import User


class SubtopicsAPIViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("generate_subtopics")

    @patch("ai_quiz.views.questions.generate_subtopics")
    def test_post_with_valid_topic(self, mock_generate_subtopics):
        mock_generate_subtopics.return_value = AsyncMock(
            subtopics=["Subtopic1", "Subtopic2"]
        )
        data = {"topic": "Science"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"subtopics": ["Subtopic1", "Subtopic2"]})

    def test_post_with_no_topic(self):
        data = {}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "`topic` is required."})

    def test_post_with_empty_topic(self):
        data = {"topic": ""}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "`topic` is required."})
