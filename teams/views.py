from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from .models import Team, Invitation
from django.contrib.auth import get_user_model
from .serializers import (
    TeamSerializer, 
    InvitationSerializer, 
    TeamMemberSerializer,
    TeamBillingSerializer 
)
from .permissions import IsTeamAdmin
from django.shortcuts import get_object_or_404

User = get_user_model()

class TeamAdminDashboardView(generics.RetrieveAPIView):
    serializer_class = TeamSerializer
    permission_classes = [IsTeamAdmin]

    def get_object(self):
        return self.request.user.administered_teams.first()

class TeamBillingView(generics.RetrieveAPIView):
    serializer_class = TeamBillingSerializer
    permission_classes = [IsTeamAdmin]

    def get_object(self):
        return self.request.user.administered_teams.first()

# --- MODIFIED VIEW ---
class TeamMemberViewSet(viewsets.ModelViewSet): # <-- Changed from ReadOnly
    """
    Lists, retrieves, and removes members of the admin's team.
    GET /api/team/members/
    GET /api/team/members/<id>/
    DELETE /api/team/members/<id>/ (to remove)
    """
    serializer_class = TeamMemberSerializer
    permission_classes = [IsTeamAdmin]
    
    # We only want GET and DELETE, not POST/PUT
    http_method_names = ['get', 'delete', 'head', 'options']

    def get_queryset(self):
        team = self.request.user.administered_teams.first()
        if team:
            return team.members.all()
        return User.objects.none()

    def destroy(self, request, *args, **kwargs):
        """
        This is the 'remove member' function (handles DELETE)
        """
        member = self.get_object()
        
        # Safety check: admin can't remove themselves
        if member == request.user:
            return Response(
                {"error": "You cannot remove yourself from the team."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Unlink the user from the team
        member.team = None
        member.user_type = 'SUBSCRIBER'
        # TODO: We also need to cancel their individual access
        # For now, we'll just unlink them.
        member.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class InvitationViewSet(viewsets.ModelViewSet):
    serializer_class = InvitationSerializer
    permission_classes = [IsTeamAdmin]
    http_method_names = ['get', 'post', 'delete', 'head', 'options'] # Added delete

    def get_queryset(self):
        team = self.request.user.administered_teams.first()
        if team:
            return team.invitations.all().order_by('-created_at')
        return Invitation.objects.none()

    def perform_create(self, serializer):
        team = self.request.user.administered_teams.first()
        serializer.save(
            team=team,
            sent_by=self.request.user
        )
