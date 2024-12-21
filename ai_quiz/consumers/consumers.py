import json

from channels.db import database_sync_to_async, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from django.utils import timezone

from ai_quiz.consumers.event_handlers import (
    NextQuestionEventHandler,
    PlayerReadyEventHandler,
    PlayerWaitingEventHandler,
    QuestionAnsweredEventHandler,
)
from ai_quiz.models import Game, Participant, Question, Room
from ai_quiz.serializers import QuestionSerializer
from users.authenticators import aget_authenticated_user


class RoomConsumer(AsyncWebsocketConsumer):
    event_handlers = {
        "player_ready": PlayerReadyEventHandler,
        "player_waiting": PlayerWaitingEventHandler,
        "next_question": NextQuestionEventHandler,
        "question_answered": QuestionAnsweredEventHandler,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_code = None
        self._init_event_handlers()

    def _init_event_handlers(self):
        for event_type in self.event_handlers:
            self.event_handlers[event_type] = self.event_handlers[event_type](
                consumer=self
            )

    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]

        await self.channel_layer.group_add(self.room_code, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        username = getattr(self, "username", None)
        if username:
            await self.send_data_to_room(
                {"type": "player_disconnected", "username": username}
            )
            participants = await database_sync_to_async(Participant.objects.filter)(
                Q(user__username=self.username) | Q(guest_user__username=self.username),
                room__room_code=self.room_code,
            )
            if not await participants.aexists():
                return
            participant = await participants.afirst()
            participant.status = "inactive"
            await participant.asave()
            await self.send_all_player_names()
        await self.channel_layer.group_discard(self.room_code, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data["type"]
        if event_type == "player_ready":
            await self.event_handlers[event_type].handle(data)
        elif event_type == "player_waiting":
            await self.handle_player_waiting(data)
        elif event_type == "next_question":
            await self.handle_next_question(data)
        elif event_type == "question_answered":
            await self.handle_question_answered(data)
        elif event_type == "question_skipped":
            # TODO: Implement this
            pass
        else:
            raise ValueError("Invalid event type")

    async def send_data_to_room(self, data):
        await self.channel_layer.group_send(
            self.room_code, {"type": "room_message", "event": data}
        )

    async def send_data_to_user(self, data):
        await self.channel_layer.send(
            self.channel_name, {"type": "room_message", "event": data}
        )

    @sync_to_async
    def get_all_participants(self):
        room = Room.objects.filter(room_code=self.room_code)
        if room.exists():
            participants = room.first().participants.filter(~Q(status="inactive"))
            return [p.user.username for p in participants if p.user] + [
                p.guest_user.username for p in participants if p.guest_user
            ]

    async def send_all_player_names(self):
        usernames = await self.get_all_participants()
        await self.send_data_to_room({"type": "all_players", "usernames": usernames})

    @database_sync_to_async
    def get_current_game(self):
        games = Game.objects.filter(
            room__room_code=self.room_code, status="in_progress"
        )
        if not games.exists():
            return None
        return games.latest("created_at")

    @database_sync_to_async
    def get_all_questions_from_game(self, game):
        questions = game.questions.all()
        len_questions = len(questions)
        return questions, len_questions

    async def get_next_question(self):
        game = await self.get_current_game()

        questions, len_questions = await self.get_all_questions_from_game(game)
        if game.current_question < len_questions:
            new_question = questions[game.current_question]
            game.current_question += 0  # TODO: Fix this to 1
            await game.asave()
            return new_question
        # This means the game is over
        game.status = "finished"
        game.ended_at = timezone.now()
        game.save()
        # TODO: Reset the participant scores to 0
        return None

    async def handle_next_question(self, data):
        token = data.get("token")
        if not token:
            await self.send_error("No token found.")
            return
        user = await aget_authenticated_user(token)
        if user is None:
            await self.send_error("Invalid token.")
            return

        await self.send_data_to_user({"success": "Authenticated."})

        question = await self.get_next_question()
        if question is not None:
            question_serializer = QuestionSerializer(question)
            await self.send_data_to_room(
                {
                    "type": "next_question",
                    "event": question_serializer.data,
                }
            )
        else:
            await self.send_data_to_room({"type": "all_questions_done"})

    async def handle_question_answered(self, data):
        username = getattr(self, "username", None)
        if username:
            question_id = data.get("questionId")
            answer = data.get("answer")
            if not question_id or not answer:
                await self.send_data_to_user(
                    {"error": "questionId and answer are required."}
                )
                return

            try:
                game = await self.get_current_game()
                current_question = await game.questions.aget(id=question_id)
            except Question.DoesNotExist:
                await self.send_data_to_user(
                    {"error": f"Invalid question id: {question_id}"}
                )
                return
            participant = await Participant.objects.aget(
                Q(user__username=username) | Q(guest_user__username=username),
                room__room_code=self.room_code,
            )

            leaderboard = await database_sync_to_async(lambda: game.leaderboard)()

            if current_question.correct_answer == answer:
                # TODO: Separate out the participant correct answers and wrong answers variables to leaderboard
                participant.correct_answers += 1
                participant.score += 1  # TODO: Update the score based on the timestamp
                leaderboard.data[username] = participant.score

                await self.send_data_to_user(
                    {
                        "type": "answer_validation",
                        "event": {"answer": answer, "isCorrect": True},
                    }
                )
            else:
                participant.wrong_answers += 1
                await self.send_data_to_user(
                    {
                        "type": "answer_validation",
                        "event": {"answer": answer, "isCorrect": False},
                    }
                )
            await self.send_data_to_room(
                {
                    "type": "leaderboard_update",
                    "data": leaderboard.data,
                }
            )
            await participant.asave()
            await leaderboard.asave()

    @sync_to_async
    def update_participant(self, username, status="ready"):
        participants = Participant.objects.filter(
            Q(user__username=username) | Q(guest_user__username=username),
            room__room_code=self.room_code,
        )
        if participants.exists():
            participant = participants.first()
            if participant.status != status:
                participant.status = status
                participant.save()
            return participant
        return None

    async def handle_player_waiting(self, data):
        # If player is waiting, update the status in the database
        # and broadcast a message to all the users in the room using event type "player_waiting"
        # TODO: Add a check to see if the game has started. If yes, refuse to let the player wait
        username = getattr(self, "username", None)
        if not username:
            print("No previous username found")
            await self.send_data_to_user({"error": "You need to be ready to wait."})
            return

        participant = await self.update_participant(username, status="waiting")
        if participant:
            await self.send_data_to_room(
                {"type": "player_waiting", "username": username}
            )

    async def handle_player_ready(self, data):
        # If player is ready, update the status in the database
        # and broadcast a message to all the users in the room using event type "player_ready"
        # TODO: Add a check to see if the game has started. If yes, refuse to let the player get ready
        username = data["username"]
        self.username = username
        participant = await self.update_participant(username, status="ready")
        if participant:
            await self.send_data_to_room({"type": "player_ready", "username": username})
        await self.send_all_player_names()

    async def send_error(self, message):
        await self.send_data_to_user({"error": message})

    async def room_message(self, event):
        message = event["event"]
        await self.send(text_data=json.dumps({"message": message}))
