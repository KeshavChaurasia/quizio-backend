import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import (
    Challenge,
    ChallengeParticipant,
    Round,
    ChallengeQuestion,
    AnswerSubmission,
)
from .serializers import (
    ChallengeSerializer,
    ChallengeParticipantSerializer,
    RoundSerializer,
    ChallengeQuestionSerializer,
    AnswerSubmissionSerializer,
)
from .permissions import IsHost


class ChallengeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing challenges.
    """

    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Override the perform_create method to set the host and generate a join_token.
        """
        # Automatically set the host to the current user
        serializer.validated_data["host"] = self.request.user

        # Generate a unique token for joining the challenge
        join_token = uuid.uuid4()
        serializer.validated_data["join_token"] = join_token

        # Save the challenge object with the generated join_token
        serializer.save()

    def create(self, request, *args, **kwargs):
        # Ensure the user is the host of the challenge
        data = request.data
        data["host"] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        """
        Allow a user to join a challenge.
        """
        challenge = self.get_object()
        user = request.user

        # Check if the user is already a participant
        if ChallengeParticipant.objects.filter(
            challenge=challenge, user=user
        ).exists():
            return Response(
                {"detail": "You are already a participant in this challenge."},
                status=400,
            )

        # Add the user as a participant
        participant = ChallengeParticipant.objects.create(
            challenge=challenge, user=user
        )
        return Response(
            {"detail": f"{user.username} joined the challenge!"},
            status=201,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsHost],
    )
    def add_round(self, request, pk=None):
        """
        Add a new round to a challenge.
        """
        challenge = self.get_object()
        data = request.data
        data["challenge"] = challenge.id
        serializer = RoundSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RoundViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing rounds within challenges.
    """

    queryset = Round.objects.all()
    serializer_class = RoundSerializer
    permission_classes = [IsAuthenticated, IsHost]

    def get_queryset(self):
        # Restrict rounds to those in challenges hosted by the current user
        return Round.objects.filter(challenge__host=self.request.user)


class ChallengeJoinView(APIView):
    """
    API view to join a challenge using a unique token.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        # Validate and join the challenge by token
        challenge = get_object_or_404(Challenge, join_token=token)

        # Check if the user is already a participant
        if ChallengeParticipant.objects.filter(
            challenge=challenge, user=request.user
        ).exists():
            return Response(
                {"detail": "You are already a participant in this challenge."},
                status=400,
            )

        # Add the user as a participant
        ChallengeParticipant.objects.create(
            challenge=challenge, user=request.user
        )
        return Response(
            {"detail": "Successfully joined the challenge!"}, status=201
        )


class ChallengeQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing challenge questions.
    """

    queryset = ChallengeQuestion.objects.all()
    serializer_class = ChallengeQuestionSerializer
    permission_classes = [IsAuthenticated, IsHost]

    def get_queryset(self):
        # Restrict questions to those in challenges hosted by the current user
        return ChallengeQuestion.objects.filter(
            challenge__host=self.request.user
        )


class AnswerSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing answer submissions by participants.
    """

    queryset = AnswerSubmission.objects.all()
    serializer_class = AnswerSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Ensure that only active participants can submit answers
        data = request.data
        participant = get_object_or_404(
            ChallengeParticipant, challenge=data["challenge"], user=request.user
        )
        if not participant.active:
            return Response(
                {
                    "detail": "You are not allowed to submit answers for this challenge."
                },
                status=403,
            )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
