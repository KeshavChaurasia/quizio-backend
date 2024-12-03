from rest_framework.permissions import BasePermission


class IsHost(BasePermission):
    """
    Custom permission to check if the user is the host of a challenge.
    """

    def has_object_permission(self, request, view, obj):
        # The user must be the host of the challenge to have permission
        return obj.host == request.user
