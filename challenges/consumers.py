
# TODO: Convert all sync calls to async database calls
# eg. self.challenge.current_question -> await self.get_current_question(self.challenge)
import asyncio
import json
import logging
from datetime import datetime

import jwt
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from quiz.models import Answer
from .models import (
    AnswerSubmission,
    Challenge,
    ChallengeParticipant,
    ChallengeQuestion,
    ChallengeEvent,
    Round,
)

logger = logging.getLogger(__name__)


class ChallengeConsumer(AsyncWebsocketConsumer):
    """WebSocket Consumer for managing real-time challenge functionality."""
    @sync_to_async
    def get_current_question(self, challenge):
        # Explicitly fetch the current_question (this will be an ORM query)
        return challenge.current_question
    async def connect(self):
        """Handle WebSocket connection."""
        self.challenge_token = self.scope["url_route"]["kwargs"]["challenge_token"]
        try:
            self.challenge = await sync_to_async(Challenge.objects.get)(join_token=self.challenge_token)
        except Challenge.DoesNotExist:
            logger.error(f"Challenge with token {self.challenge_token} not found.")
            await self.close()
            return

        token = self.scope["query_string"].decode().split("=", 1)[-1]
        self.user = await self.authenticate_user(token)

        if self.user or not token:  # Allow anonymous participants
            self.room_group_name = f"challenge_{self.challenge_token}"

            # For anonymous users, prompt for a username
            if not self.user:
                self.username = self.scope.get("query_string", "").decode().split("username=")[-1]
                if not self.username:
                    self.username = f"Anonymous_{datetime.utcnow().timestamp()}"
                self.participant = await self.add_user_to_challenge(self.username)
            else:
                self.participant = await self.add_user_to_challenge()

            await self.accept()

            # Log event
            await self.log_event("user_joined", metadata={"username": self.username if not self.user else self.user.username})

            # Handle active challenge state
            if self.challenge.status == "active":
                self.current_question = await self.get_current_question(self.challenge)
                await self.start_timer(self.current_question.time_limit)
        else:
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "participant"):
            await self.remove_user_from_challenge()
            await self.log_event(
                "user_left",
                metadata={
                    "username": self.user.username if self.user else "anonymous"
                },
            )

    async def authenticate_user(self, token):
        """Authenticate user using JWT token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=["HS256"]
            )
            if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
                raise jwt.ExpiredSignatureError
            user_id = payload["user_id"]
            return await sync_to_async(get_user_model().objects.get)(id=user_id)
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            get_user_model().DoesNotExist,
        ):
            logger.warning("Invalid or expired token.")
            return None

    async def add_user_to_challenge(self, username=None):
        """Add user to the challenge."""
        participant = await sync_to_async(ChallengeParticipant.objects.get_or_create)(
            challenge=self.challenge,
            user=self.user if self.user else None,
            username=username if not self.user else None,  # Only set username for anonymous users
        )
        return participant[0]

    @sync_to_async
    def remove_user_from_challenge(self):
        """Remove user from the challenge."""
        ChallengeParticipant.objects.filter(challenge=self.challenge, user=self.user, username=self.username).delete()

    async def receive(self, text_data):
        """Handle WebSocket messages."""
        try:
            data = json.loads(text_data)
            action = data.get("action")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON data received.")
            return

        if action == "answer_submission":
            await self.handle_answer_submission(data)
        elif action == "leave_challenge":
            await self.disconnect(close_code=1000)
        else:
            logger.warning(f"Unhandled action: {action}")

    async def handle_answer_submission(self, data):
        """Process answer submission."""
        selected_answers = data.get("selected_answers", [])
        if not selected_answers:
            logger.warning("No answers provided.")
            return

        await self.store_answer(
            self.participant, self.challenge.current_question, selected_answers
        )
        await self.log_event(
            "answer_submitted", metadata={"answers": selected_answers}
        )

        if await self.check_all_answered():
            await self.end_question()

    @sync_to_async
    def check_all_answered(self):
        """Check if all participants have answered the current question."""
        participants = ChallengeParticipant.objects.filter(
            challenge=self.challenge
        )
        submissions = AnswerSubmission.objects.filter(
            question=self.challenge.current_question,
            participant__in=participants,
        )
        return submissions.count() == participants.count()

    def calculate_points(self, challenge_question, submission_time):
        """Calculate points based on time taken to answer."""
        time_taken = (
            submission_time - challenge_question.time_started
        ).total_seconds()
        base_points = 100
        penalty_per_second = 5
        return max(base_points - penalty_per_second * time_taken, 0)

    @sync_to_async
    def store_answer(self, participant, challenge_question, selected_answers):
        """Store the participant's answer and calculate points."""
        correct_answers = Answer.objects.filter(
            question=challenge_question.question, is_correct=True
        ).values_list("id", flat=True)

        is_correct = set(map(int, selected_answers)) == set(correct_answers)
        submission_time = now()
        points = (
            self.calculate_points(challenge_question, submission_time)
            if is_correct
            else 0
        )

        AnswerSubmission.objects.create(
            participant=participant,
            question=challenge_question,
            answer=",".join(map(str, selected_answers)),
            is_correct=is_correct,
            submitted_at=submission_time,
            time_taken=(
                submission_time - challenge_question.time_started
            ).total_seconds(),
        )
        participant.score += points
        participant.save()

    async def start_timer(self, time_limit):
        """Start a countdown timer for the current question."""
        for remaining_time in range(time_limit, -1, -1):
            await self.send_message(
                {"type": "timer_update", "remaining_time": remaining_time}
            )
            if remaining_time > 0:
                await asyncio.sleep(1)

        await self.end_question()
    
    async def end_question(self):
        """Handle the end of the question."""
        correct_answers = sync_to_async(Answer.objects.filter)(
            question=self.current_question.question, is_correct=True
        ).values_list("id", flat=True)

        await self.send_message(
            {
                "type": "question_end",
                "correct_answers": list(correct_answers),
                "message": "Time is up!",
            }
        )
        await self.log_event(
            "question_end", metadata={"correct_answers": list(correct_answers)}
        )

        await sync_to_async(self.challenge.next_question)()
        if self.challenge.status == "active":
            await self.send_message(
                {
                    "type": "new_question",
                    "question": {
                        "id": self.challenge.current_question.id,
                        "text": self.challenge.current_question.question.question_text,
                        "time_limit": self.challenge.current_question.time_limit,
                    },
                }
            )
            await self.start_timer(self.challenge.current_question.time_limit)

    async def send_message(self, message):
        """Send a JSON message to the WebSocket."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "send_to_websocket", "message": json.dumps(message)},
        )

    async def send_to_websocket(self, event):
        """Send a message to the WebSocket."""
        await self.send(text_data=event["message"])

    @sync_to_async
    def log_event(self, event_type, metadata=None):
        """Log an event to the database."""
        ChallengeEvent.objects.create(
            challenge=self.challenge,
            participant=self.participant if self.user else None,
            event_type=event_type,
            metadata=metadata,
        )
