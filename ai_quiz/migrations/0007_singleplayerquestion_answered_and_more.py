# Generated by Django 5.1.4 on 2024-12-22 19:25

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_quiz", "0006_question_difficulty_singleplayerquestion_difficulty"),
        ("users", "0003_remove_user_role"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="singleplayerquestion",
            name="answered",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="singleplayerquestion",
            name="skipped",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="answer",
            name="is_correct",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.CreateModel(
            name="SinglePlayerAnswer",
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
                ("answer", models.CharField(max_length=512)),
                ("is_correct", models.BooleanField(default=False)),
                (
                    "submitted_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "guest_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="single_player_answers",
                        to="users.guestuser",
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="answers",
                        to="ai_quiz.singleplayerquestion",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="single_player_answers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
