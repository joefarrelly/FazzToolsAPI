from rest_framework.permissions import BasePermission


class IsSessionUser(BasePermission):
    """Allows access only if the session user_id matches the ?user= query param."""

    def has_permission(self, request, view):
        session_user = request.session.get("user_id")
        if not session_user:
            return False
        return session_user == request.query_params.get("user")
