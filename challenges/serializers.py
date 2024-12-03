from rest_framework import serializers
from .models import Challenge, ChallengeParticipant, Round, ChallengeQuestion, AnswerSubmission


class ChallengeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Challenge model.
    """
    host = serializers.StringRelatedField(read_only=True)  # Display host as username
    join_link = serializers.SerializerMethodField()  # Generate join link

    class Meta:
        model = Challenge
        fields = "__all__"
        read_only_fields = ['join_token', 'host', 'created_at']

    def get_join_link(self, obj):
        # Generate a join link using the challenge's join_token
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/challenges/join/{obj.join_token}/')
        return None


class ChallengeParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer for ChallengeParticipant model.
    """
    user = serializers.StringRelatedField()  # Display participant's username

    class Meta:
        model = ChallengeParticipant
        fields = "__all__"
        read_only_fields = ['joined_at']


class RoundSerializer(serializers.ModelSerializer):
    """
    Serializer for the Round model.
    """
    challenge = serializers.StringRelatedField()  # Display challenge title

    class Meta:
        model = Round
        fields = "__all__"
        read_only_fields = ['created_at']


class ChallengeQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for ChallengeQuestion model.
    """
    round = serializers.StringRelatedField()  # Display round title
    options = serializers.JSONField()  # Handle multimedia options as JSON

    class Meta:
        model = ChallengeQuestion
        fields = "__all__"

class AnswerSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for AnswerSubmission model.
    """
    participant = serializers.StringRelatedField()  # Display participant's username
    question = serializers.StringRelatedField()  # Display question text

    class Meta:
        model = AnswerSubmission
        fields = "__all__"
        read_only_fields = ['submitted_at']
