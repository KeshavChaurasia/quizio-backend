# Generated by Django 5.1.4 on 2024-12-22 18:59

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_quiz", "0003_topic_rename_text_question_question_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="room",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="games",
                to="ai_quiz.room",
            ),
        ),
        migrations.AlterField(
            model_name="game",
            name="status",
            field=models.CharField(
                choices=[
                    ("waiting", "Waiting"),
                    ("in_progress", "In Progress"),
                    ("finished", "Finished"),
                ],
                default="waiting",
                max_length=15,
            ),
        ),
        migrations.CreateModel(
            name="SinglePlayerGame",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("waiting", "Waiting"),
                            ("in_progress", "In Progress"),
                            ("finished", "Finished"),
                        ],
                        default="waiting",
                        max_length=15,
                    ),
                ),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("current_question", models.IntegerField(default=0)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="single_player_games",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SinglePlayerQuestion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("question", models.CharField(max_length=512)),
                ("subtopic", models.CharField(blank=True, max_length=512, null=True)),
                ("options", models.JSONField()),
                ("correct_answer", models.CharField(max_length=512)),
                ("timer", models.IntegerField(default=30)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="questions",
                        to="ai_quiz.singleplayergame",
                    ),
                ),
                (
                    "topic",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="single_player_question_topic",
                        to="ai_quiz.topic",
                    ),
                ),
            ],
        ),
    ]
