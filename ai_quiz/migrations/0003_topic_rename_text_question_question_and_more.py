# Generated by Django 5.1.4 on 2024-12-20 12:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_quiz", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Topic",
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
                ("name", models.CharField(max_length=512, unique=True)),
                ("subtopics", models.JSONField(blank=True, default=list, null=True)),
            ],
        ),
        migrations.RenameField(
            model_name="question",
            old_name="text",
            new_name="question",
        ),
        migrations.AddField(
            model_name="question",
            name="subtopic",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name="question",
            name="topic",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="question_topic",
                to="ai_quiz.topic",
            ),
        ),
    ]
