from ai_quiz import models
from django.contrib import admin

admin.site.register(models.Room)
admin.site.register(models.Game)
admin.site.register(models.Question)
admin.site.register(models.Participant)
admin.site.register(models.Leaderboard)
admin.site.register(models.Answer)
