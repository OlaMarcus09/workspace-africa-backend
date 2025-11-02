from rest_framework import permissions

class IsPartnerUser(permissions.BasePermission):
    """
    Custom permission to only allow users with the 'PARTNER' type
    and a linked managed_space.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated, is a PARTNER,
        # and has a space assigned to them.
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'PARTNER' and
            request.user.managed_space is not None
        )
