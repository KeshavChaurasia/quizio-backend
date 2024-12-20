from ai_quiz import models
from django.contrib import admin


# Define an Inline for the Question model
class QuestionInline(admin.TabularInline):
    model = models.Question
    extra = 1  # This defines how many empty forms should be displayed by default


# Define the Admin class for Game
class GameAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]  # Add the QuestionInline to GameAdmin


admin.site.register(models.Room)
admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Question)
admin.site.register(models.Participant)
admin.site.register(models.Leaderboard)
admin.site.register(models.Answer)
admin.site.register(models.Topic)
