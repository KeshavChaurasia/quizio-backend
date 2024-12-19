from users import models
from django.contrib import admin

admin.site.register(models.User)
admin.site.register(models.Profile)
admin.site.register(models.GuestUser)
