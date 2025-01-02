# Generated by Django 5.1.4 on 2025-01-02 14:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_quiz", "0007_singleplayerquestion_answered_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="participant",
            name="avatar_seed",
            field=models.CharField(default="", max_length=50),
        ),
        migrations.AddField(
            model_name="participant",
            name="avatar_style",
            field=models.CharField(default="Circle", max_length=50),
        ),
        migrations.AlterField(
            model_name="game",
            name="status",
            field=models.CharField(
                choices=[
                    ("waiting", "Waiting"),
                    ("in_progress", "In Progress"),
                    ("finished", "Finished"),
                    ("aborted", "Aborted"),
                ],
                default="waiting",
                max_length=15,
            ),
        ),
    ]
