# Generated by Django 5.1.3 on 2024-12-04 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0005_rename_timer_challengequestion_time_limit_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='challengeparticipant',
            name='username',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
