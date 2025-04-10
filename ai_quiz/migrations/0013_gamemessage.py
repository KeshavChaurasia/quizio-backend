# Generated by Django 5.1.4 on 2025-01-03 19:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_quiz", "0012_question_updated_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="GameMessage",
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
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chat_messages",
                        to="ai_quiz.game",
                    ),
                ),
                (
                    "participant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chat_messages",
                        to="ai_quiz.participant",
                    ),
                ),
            ],
        ),
    ]
