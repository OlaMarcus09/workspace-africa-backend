from rest_framework import serializers
from .models import Team, Invitation
from users.serializers import TeamMemberSerializer # Import our new serializer

class TeamSerializer(serializers.ModelSerializer):
    """
    Serializer for the Team Admin's team.
    """
    members = TeamMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ('id', 'name', 'admin', 'members')

class InvitationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and listing invitations.
    """
    # We want to show the email, not just the ID
    sent_by = serializers.EmailField(source='sent_by.email', read_only=True)

    class Meta:
        model = Invitation
        fields = ('id', 'team', 'email', 'status', 'created_at', 'sent_by')
        read_only_fields = ('id', 'team', 'status', 'created_at', 'sent_by')

    def validate_email(self, value):
        # We need to find the admin's team to check against
        admin_user = self.context['request'].user
        team = admin_user.administered_teams.first()
        
        if not team:
            raise serializers.ValidationError("You do not admin a team.")
            
        # Check if user is already on the team
        if team.members.filter(email=value).exists():
            raise serializers.ValidationError("User is already a member of this team.")
        
        # Check if there's already a pending invite
        if Invitation.objects.filter(team=team, email=value, status='PENDING').exists():
            raise serializers.ValidationError("A pending invitation for this email already exists.")
            
        return value
