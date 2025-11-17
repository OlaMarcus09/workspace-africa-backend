from rest_framework import generics, status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import Team, Invitation
from users.models import CustomUser
from spaces.models import Plan, Subscription
import secrets

class TeamSignupView(generics.CreateAPIView):
    permission_classes = []  # Allow unauthenticated access
    
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            plan_data = data.get('plan', {})
            
            # Check if admin email already exists
            if CustomUser.objects.filter(email=data.get('adminEmail')).exists():
                return Response(
                    {"error": "A user with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find the plan (you might want to create team plans in your database)
            # For now, we'll use a placeholder plan
            plan, created = Plan.objects.get_or_create(
                name=plan_data.get('name', 'Team Pro'),
                defaults={
                    'price_ngn': float(plan_data.get('price', '45000').replace('₦', '').replace(',', '')),
                    'included_days': plan_data.get('daysPerMember', 18),
                    'access_tier': 'PREMIUM'
                }
            )
            
            # Create temporary password
            temp_password = secrets.token_urlsafe(12)
            
            # Create team admin user
            admin_user = CustomUser.objects.create_user(
                email=data.get('adminEmail'),
                username=data.get('adminEmail').split('@')[0],
                password=temp_password,
                first_name=data.get('adminName', '').split(' ')[0],
                last_name=' '.join(data.get('adminName', '').split(' ')[1:]),
                user_type=CustomUser.UserType.TEAM_ADMIN
            )
            
            # Create team
            team = Team.objects.create(
                name=data.get('companyName'),
                admin=admin_user
            )
            
            # Create subscription for team
            subscription = Subscription.objects.create(
                plan=plan,
                is_active=True
                # Note: For teams, we don't link to user but to team
                # You might need to adjust your Subscription model
            )
            
            # Link subscription to team
            team.subscription = subscription
            team.save()
            
            # Link admin to team (as a member as well)
            admin_user.team = team
            admin_user.save()
            
            # Send welcome email
            send_mail(
                'Welcome to Workspace Africa Teams!',
                f'''
                Hello {data.get('adminName')},
                
                Welcome to Workspace Africa Teams! Your team plan has been activated.
                
                Team: {data.get('companyName')}
                Plan: {plan_data.get('name')}
                Seats: {plan_data.get('seats')} members
                Access: {plan_data.get('daysPerMember')} days per member/month
                
                Next Steps:
                1. Login to your team dashboard
                2. Invite your team members
                3. Start using workspaces across Nigeria
                
                Login: {settings.FRONTEND_URL}/login
                
                Best regards,
                Workspace Africa Team
                ''',
                settings.DEFAULT_FROM_EMAIL,
                [data.get('adminEmail')],
                fail_silently=True,
            )
            
            return Response(
                {
                    "message": "Team created successfully!",
                    "team_id": team.id,
                    "admin_email": admin_user.email,
                    "login_url": f"{settings.FRONTEND_URL}/login"
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {"error": f"Team signup failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
