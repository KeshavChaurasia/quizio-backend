from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from users import views

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", views.register_user, name="register"),
    path("profile/", views.user_profile, name="user_profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
]
