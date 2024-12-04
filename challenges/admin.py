from django.contrib import admin
from .models import Challenge, ChallengeParticipant, Round, ChallengeQuestion, AnswerSubmission


class ChallengeParticipantInline(admin.TabularInline):
    """
    Inline for displaying ChallengeParticipants within the Challenge admin.
    """
    model = ChallengeParticipant
    extra = 0
    readonly_fields = ('user', 'joined_at', 'active')
    can_delete = False


class ChallengeQuestionInline(admin.TabularInline):
    """
    Inline for displaying ChallengeQuestions within the Round admin.
    """
    model = ChallengeQuestion
    extra = 0
    # readonly_fields = ('question_text', 'question_media_url', 'options', 'correct_answers')
    can_delete = False


class ChallengeAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Challenge model.
    """
    list_display = ('title', 'host', 'created_at', 'join_token')
    list_filter = ('host', 'created_at')
    search_fields = ('title', 'description')
    inlines = [ChallengeParticipantInline]
    readonly_fields = ('join_token', 'host', 'created_at')

    def save_model(self, request, obj, form, change):
        """
        Override the save_model method to set the host automatically to the current user.
        """
        if not obj.host:
            obj.host = request.user
        obj.save()


class RoundAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Round model.
    """
    list_display = ('title', 'challenge', 'created_at')
    list_filter = ('challenge', 'created_at')
    search_fields = ('title',)
    inlines = [ChallengeQuestionInline]
    readonly_fields = ('created_at',)


class ChallengeQuestionAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ChallengeQuestion model.
    """
    # list_display = ('round', 'question_text', 'question_media_url')
    list_filter = ('round',)
    search_fields = ('question_text',)
    # readonly_fields = ('created_at',)


class AnswerSubmissionAdmin(admin.ModelAdmin):
    """
    Admin configuration for the AnswerSubmission model.
    """
    # list_display = ('participant', 'question', 'selected_answers', 'submitted_at')
    list_filter = ('participant', 'submitted_at')
    search_fields = ('question__question_text')
    readonly_fields = ('submitted_at',)


# Register the models and their respective admin configurations
admin.site.register(Challenge, ChallengeAdmin)
admin.site.register(ChallengeParticipant)
admin.site.register(Round, RoundAdmin)
admin.site.register(ChallengeQuestion, ChallengeQuestionAdmin)
admin.site.register(AnswerSubmission, AnswerSubmissionAdmin)
