from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChallengeViewSet, RoundViewSet, ChallengeJoinView, ChallengeQuestionViewSet, AnswerSubmissionViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'challenges', ChallengeViewSet, basename='challenge')
router.register(r'rounds', RoundViewSet, basename='round')
router.register(r'questions', ChallengeQuestionViewSet, basename='question')
router.register(r'answers', AnswerSubmissionViewSet, basename='answer')

urlpatterns = [
    # The base API routes for our viewsets
    path('api/', include(router.urls)),

    # Custom path for joining a challenge via a unique token
    path('api/challenges/join/<uuid:token>/', ChallengeJoinView.as_view(), name='challenge-join'),
]
