# Generated by Django 5.1.4 on 2025-01-02 21:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_quiz", "0011_remove_participant_correct_answers_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
