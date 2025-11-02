from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from .models import Team, Invitation
from django.contrib.auth import get_user_model
from .serializers import TeamSerializer, InvitationSerializer, TeamMemberSerializer
from .permissions import IsTeamAdmin
from django.shortcuts import get_object_or_404

User = get_user_model()

class TeamAdminDashboardView(generics.RetrieveAPIView):
    """
    The main dashboard for the Team Admin.
    Shows their team, members, and pending invites.
    GET /api/team/dashboard/
    """
    serializer_class = TeamSerializer
    permission_classes = [IsTeamAdmin]

    def get_object(self):
        # The permission check already confirms they admin a team.
        # We just get the first team they admin.
        return self.request.user.administered_teams.first()

class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lists and retrieves members of the admin's team.
    GET /api/team/members/
    GET /api/team/members/<id>/
    """
    serializer_class = TeamMemberSerializer
    permission_classes = [IsTeamAdmin]

    def get_queryset(self):
        # Get the admin's team
        team = self.request.user.administered_teams.first()
        if team:
            # Return only members of that team
            return team.members.all()
        return User.objects.none() # Return empty if no team

class InvitationViewSet(viewsets.ModelViewSet):
    """
    Manages invitations for the admin's team.
    POST /api/team/invites/ (to create)
    GET /api/team/invites/ (to list)
    DELETE /api/team/invites/<id>/ (to revoke)
    """
    serializer_class = InvitationSerializer
    permission_classes = [IsTeamAdmin]

    def get_queryset(self):
        # Get the admin's team
        team = self.request.user.administered_teams.first()
        if team:
            # Return only invites for that team
            return team.invitations.all().order_by('-created_at')
        return Invitation.objects.none()

    def perform_create(self, serializer):
        # When creating an invite, automatically assign the team and sent_by
        team = self.request.user.administered_teams.first()
        serializer.save(
            team=team,
            sent_by=self.request.user
        )
