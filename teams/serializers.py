from rest_framework import serializers
from .models import Team, Invitation
from users.serializers import TeamMemberSerializer
# Import the subscription serializer from the 'spaces' app
from spaces.serializers import SubscriptionSerializer 

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
    sent_by = serializers.EmailField(source='sent_by.email', read_only=True)

    class Meta:
        model = Invitation
        fields = ('id', 'team', 'email', 'status', 'created_at', 'sent_by')
        read_only_fields = ('id', 'team', 'status', 'created_at', 'sent_by')

    def validate_email(self, value):
        admin_user = self.context['request'].user
        team = admin_user.administered_teams.first()
        
        if not team:
            raise serializers.ValidationError("You do not admin a team.")
            
        if team.members.filter(email=value).exists():
            raise serializers.ValidationError("User is already a member of this team.")
        
        if Invitation.objects.filter(team=team, email=value, status='PENDING').exists():
            raise serializers.ValidationError("A pending invitation for this email already exists.")
            
        return value

# --- NEW SERIALIZER ---
class TeamBillingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Team Admin's billing page.
    Shows the team's subscription details.
    """
    # Use the serializer we already built in the 'spaces' app
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = Team
        fields = ('id', 'name', 'subscription')
