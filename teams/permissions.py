from rest_framework import permissions

class IsTeamAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users with the 'TEAM_ADMIN' type
    and a linked team.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated, is a TEAM_ADMIN,
        # and has a team assigned to them.
        user = request.user
        if not (user and user.is_authenticated):
            return False
        
        # Check if they are a team admin for *any* team
        return (
            user.user_type == 'TEAM_ADMIN' and
            user.administered_teams.exists()
        )

    def has_object_permission(self, request, view, obj):
        # For object-level permissions (e.g., editing a specific team)
        # make sure they are the admin *of that specific team*.
        user = request.user
        if not self.has_permission(request, view):
            return False
        
        # If the object is a Team
        if hasattr(obj, 'admin'):
            return obj.admin == user
        
        # If the object is a member (CustomUser) or Invitation
        if hasattr(obj, 'team'):
            return obj.team.admin == user
            
        return False
