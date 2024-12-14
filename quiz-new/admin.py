# Register your models here.
from django.contrib import admin
from .models import Quiz, Question, Answer, Category, QuizAttempt
from django.utils.html import format_html
from django.urls import reverse


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2  # Number of extra empty answer fields


class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "question_type")
    filter_horizontal = ("quizzes",)  # Allow selecting multiple quizzes for a question
    inlines = [AnswerInline]


class QuestionInline(admin.TabularInline):
    model = (
        Question.quizzes.through
    )  # Use the intermediary model for the many-to-many relationship
    extra = 0  # No extra blank rows by default
    verbose_name = "Associated Question"
    verbose_name_plural = "Associated Questions"

    def question_link(self, obj):
        url = reverse("admin:quiz_question_change", args=[obj.question.id])
        return format_html('<a href="{}">{}</a>', url, obj.question.question_text)

    question_link.short_description = "Question"

    fields = ("question_link",)  # Only show the link field
    readonly_fields = ("question_link",)  # Make the field read-only


class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "created_at")
    filter_horizontal = ("categories",)  # Allow selecting multiple categories
    inlines = [QuestionInline]


class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_link",
        "quiz_link",
        "score",
        "total_questions",
        "created_at",
    )
    readonly_fields = (
        "user_link",
        "quiz_link",
        "score",
        "total_questions",
        "created_at",
        "questions_list",
    )

    def user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user_link.short_description = "User"

    def quiz_link(self, obj):
        url = reverse("admin:quiz_quiz_change", args=[obj.quiz.id])
        return format_html('<a href="{}">{}</a>', url, obj.quiz.title)

    quiz_link.short_description = "Quiz"

    def questions_list(self, obj):
        questions = obj.quiz.questions.all()
        links = [
            format_html(
                '<a href="{}">{}</a>',
                reverse("admin:quiz_question_change", args=[q.id]),
                q.question_text,
            )
            for q in questions
        ]
        return format_html("<br>".join(links))

    questions_list.short_description = "Questions"


admin.site.register(Category)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)
