# Generated by Django 5.1.4 on 2024-12-22 19:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_quiz", "0004_alter_game_room_alter_game_status_singleplayergame_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="topic",
            name="name",
            field=models.CharField(max_length=512),
        ),
    ]
