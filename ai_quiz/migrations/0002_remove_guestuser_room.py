# Generated by Django 5.1.3 on 2024-12-14 19:21

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ai_quiz", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="guestuser",
            name="room",
        ),
    ]
