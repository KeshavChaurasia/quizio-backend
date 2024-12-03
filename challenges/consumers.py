import json
import logging
from datetime import datetime

import jwt
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import (
    AnswerSubmission,
    Challenge,
    ChallengeParticipant,
    ChallengeQuestion,
    Round,
)

logger = logging.getLogger(__name__)


class ChallengeConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer to handle the challenge-related real-time functionality.
    """

    async def connect(self):
        # Extract the challenge token from the URL
        self.challenge_token = self.scope["url_route"]["kwargs"][
            "challenge_token"
        ]
        try:
            self.challenge = await sync_to_async(Challenge.objects.get)(
                join_token=self.challenge_token
            )
        except Challenge.DoesNotExist:
            print(f"Challenge with token {self.challenge_token} not found.")
            await self.close()
            return
        # Get the token from the query string in the WebSocket URL

        token = self.scope["query_string"].decode()
        if token:
            try:
                token = token.split("=")[1]  # e.g., token=your-jwt-token-here
                # Decode and validate the token
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=["HS256"]
                )

                # Check if the token has expired
                if (
                    datetime.utcfromtimestamp(payload["exp"])
                    < datetime.utcnow()
                ):
                    raise jwt.ExpiredSignatureError

                # Get the user ID from the token
                user_id = payload["user_id"]
                self.user = await sync_to_async(get_user_model().objects.get)(
                    id=user_id
                )

                # Ensure the user is authenticated
                if self.user.is_authenticated:
                    # Proceed with the WebSocket connection for authenticated user
                    self.room_group_name = f"challenge_{self.challenge_token}"
                    await self.add_user_to_challenge()

                    # Accept the WebSocket connection
                    await self.accept()
                else:
                    # Reject connection if the user is not authenticated
                    await self.close()
            except jwt.ExpiredSignatureError:
                print("Token has expired.")
                await self.close()
            except jwt.InvalidTokenError:
                print("Invalid token.")
                await self.close()
            except IndexError:
                print("No token provided.")
                await self.close()
        else:
            # If the token is not provided, handle the anonymous user (they can still join)
            self.user = None  # Set the user to None for anonymous users
            self.room_group_name = f"challenge_{self.challenge_token}"
            await self.add_user_to_challenge()

            # Accept the WebSocket connection
            await self.accept()

    async def disconnect(self, close_code):
        """Handle disconnection."""
        if hasattr(self, "user") and self.user:
            # Remove the user from the challenge when they disconnect
            await self.remove_user_from_challenge()

    async def receive(self, text_data):
        """Handle messages received from WebSocket."""
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON data received.")
        action = text_data_json["action"]

        if action == "answer_submission":
            question_id = text_data_json["question_id"]
            selected_answers = text_data_json["selected_answers"]

            # Process the answer submission
            await self.process_answer_submission(question_id, selected_answers)

        elif action == "leave_challenge":
            # Handle participant leaving the challenge
            await self.remove_user_from_challenge()
            await self.close()

    # Add user to the challenge (anonymous or logged in)
    @sync_to_async
    def add_user_to_challenge(self):
        if self.user:
            # If the user is logged in, associate them with their user record
            participant, created = ChallengeParticipant.objects.get_or_create(
                challenge=self.challenge, user=self.user
            )
        else:
            # If the user is anonymous, associate them with an anonymous participant
            participant, created = ChallengeParticipant.objects.get_or_create(
                challenge=self.challenge,
                user=None,  # Anonymous user does not have a user record
            )
        return participant

    # Remove user from the challenge
    @sync_to_async
    def remove_user_from_challenge(self):
        ChallengeParticipant.objects.filter(
            challenge=self.challenge, user=self.user
        ).delete()

    # Process the answer submission
    @sync_to_async
    def process_answer_submission(self, question_id, selected_answers):
        question = ChallengeQuestion.objects.get(id=question_id)
        correct_answers = question.correct_answers.split(",")

        # Check if the submitted answers match the correct answers
        correct = set(selected_answers) == set(correct_answers)

        # Store the answer submission
        AnswerSubmission.objects.create(
            participant=self.user,
            question=question,
            selected_answers=",".join(selected_answers),
            is_correct=correct,
        )

    # Send a message to WebSocket (for broadcasting updates like the correct answer)
    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))
