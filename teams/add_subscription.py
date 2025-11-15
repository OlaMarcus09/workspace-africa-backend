from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from teams.models import Team
from spaces.models import Plan, Subscription

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_subscription_to_team(request):
    """
    Add a subscription to the current user's team
    """
    user = request.user
    
    if user.user_type != 'TEAM_ADMIN':
        return Response({
            "error": "Only Team Admin users can use this endpoint"
        }, status=400)
    
    team = user.administered_teams.first()
    if not team:
        return Response({
            "error": "User does not have a team"
        }, status=400)
    
    # Check if team already has subscription
    if team.subscription:
        return Response({
            "status": "already_has_subscription",
            "message": f"Team already has subscription: {team.subscription.plan.name}",
            "subscription_id": team.subscription.id,
            "plan_name": team.subscription.plan.name,
            "plan_price": str(team.subscription.plan.price_ngn)
        })
    
    # Create or get team plan
    team_plan, created = Plan.objects.get_or_create(
        name='Team Flex Pro',
        defaults={
            'price_ngn': 75000,
            'included_days': 15,
            'access_tier': 'PREMIUM',
            'paystack_plan_code': 'team_flex_pro'
        }
    )
    
    # Create subscription
    subscription = Subscription.objects.create(
        plan=team_plan,
        is_active=True
    )
    
    # Link subscription to team
    team.subscription = subscription
    team.save()
    
    return Response({
        "status": "subscription_created",
        "message": "Subscription added to team successfully",
        "team_id": team.id,
        "team_name": team.name,
        "subscription_id": subscription.id,
        "plan_name": team_plan.name,
        "plan_price": str(team_plan.price_ngn),
        "included_days": team_plan.included_days,
        "access_tier": team_plan.access_tier
    })
