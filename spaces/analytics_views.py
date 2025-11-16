from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Q
from .models import CheckIn, Subscription
from users.models import CustomUser
import datetime

class UserAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get user's active subscription
        active_subscription = Subscription.objects.filter(
            user=user, 
            is_active=True
        ).first()
        
        # Total check-ins (all time)
        total_checkins = CheckIn.objects.filter(user=user).count()
        
        # Monthly check-ins
        monthly_checkins = CheckIn.objects.filter(
            user=user, 
            timestamp__gte=current_month_start
        ).count()
        
        # Days used this month (distinct days with check-ins)
        days_used = CheckIn.objects.filter(
            user=user, 
            timestamp__gte=current_month_start
        ).dates('timestamp', 'day').distinct().count()
        
        # Favorite space (most visited)
        favorite_space_data = CheckIn.objects.filter(user=user).values(
            'space__name'
        ).annotate(
            visit_count=Count('id')
        ).order_by('-visit_count').first()
        
        favorite_space = favorite_space_data['space__name'] if favorite_space_data else 'None'
        
        # Weekly pattern (last 7 days)
        week_ago = now - datetime.timedelta(days=7)
        weekly_data = []
        
        for i in range(7):
            day = week_ago + datetime.timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_checkins = CheckIn.objects.filter(
                user=user,
                timestamp__range=(day_start, day_end)
            ).count()
            
            weekly_data.append({
                'day': day.strftime('%a'),
                'checkins': day_checkins
            })
        
        # Peak hours analysis
        peak_hours = []
        for hour in range(8, 19):  # 8 AM to 6 PM
            hour_checkins = CheckIn.objects.filter(
                user=user,
                timestamp__hour=hour
            ).count()
            
            if hour_checkins > 0:
                hour_label = f"{hour}-{hour+1}"
                peak_hours.append({
                    'hour': hour_label,
                    'percentage': min((hour_checkins / max(total_checkins, 1)) * 100, 100)
                })
        
        # Spaces visited (top 3)
        spaces_visited = CheckIn.objects.filter(user=user).values(
            'space__name', 'space__access_tier'
        ).annotate(
            visits=Count('id')
        ).order_by('-visits')[:3]
        
        spaces_data = []
        for space in spaces_visited:
            spaces_data.append({
                'name': space['space__name'],
                'visits': space['visits'],
                'tier': space['space__access_tier']
            })
        
        # Subscription data
        subscription_data = None
        days_remaining = 0
        total_days = 0
        
        if active_subscription:
            total_days = active_subscription.plan.included_days
            days_remaining = max(total_days - days_used, 0)
            
            subscription_data = {
                'plan_name': active_subscription.plan.name,
                'total_days': total_days,
                'days_used': days_used,
                'days_remaining': days_remaining,
                'access_tier': active_subscription.plan.access_tier
            }
        
        analytics_data = {
            'overview': {
                'total_checkins': total_checkins,
                'monthly_checkins': monthly_checkins,
                'days_used': days_used,
                'favorite_space': favorite_space,
                'member_since': user.date_joined.strftime('%b %Y')
            },
            'subscription': subscription_data,
            'monthly_stats': {
                'current': monthly_checkins,
                'previous': 0,  # You can implement comparison with previous month
                'change': 0,
                'trend': 'up' if monthly_checkins > 0 else 'neutral'
            },
            'spaces_visited': spaces_data,
            'weekly_pattern': weekly_data,
            'peak_hours': peak_hours
        }
        
        return Response(analytics_data)
