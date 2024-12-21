from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

User = get_user_model()


def __authenticate_user(token: str) -> str:
    try:
        # Validate the token using Simple JWT
        UntypedToken(token)  # Validate token
        user_id = UntypedToken(token).payload["user_id"]
        return user_id
    except Exception:
        return None


def get_authenticated_user(token: str) -> AbstractUser:
    user_id = __authenticate_user(token)
    if user_id is None:
        return None
    return User.objects.get(id=user_id)


async def aget_authenticated_user(token: str) -> AbstractUser:
    user_id = __authenticate_user(token)
    if user_id is None:
        return None
    return await User.objects.aget(id=user_id)
