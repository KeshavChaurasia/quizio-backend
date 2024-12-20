from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Profile


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_or_email = attrs.get(
            "username"
        )  # Field name 'username' is used for compatibility
        password = attrs.get("password")

        # We need to get the both the username and email of the user and store it here
        new_attrs = {"password": password}

        user = None
        # Check if the input is an email
        if "@" in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                new_attrs["email"] = username_or_email
                new_attrs["username"] = user.username
            except User.DoesNotExist:
                raise AuthenticationFailed("User with this email does not exist.")
        else:
            try:
                user = User.objects.get(username=username_or_email)
                new_attrs["username"] = username_or_email
                new_attrs["email"] = user.email
            except User.DoesNotExist:
                raise AuthenticationFailed("User with this username does not exist.")

        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect password.")

        if not user.is_active:
            raise AuthenticationFailed("User account is disabled.")

        # Generate token
        data = super().validate(new_attrs)

        data["user"] = {"id": user.id, "username": user.username, "email": user.email}
        return data


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["bio", "avatar"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]
