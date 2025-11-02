from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from .models import Plan, PartnerSpace, CheckIn, CheckInToken, Subscription
from .serializers import (
    PlanSerializer, 
    PartnerSpaceSerializer, 
    CheckInTokenSerializer,
    CheckInValidationSerializer
)
from users.serializers import UserProfileSerializer 
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from .permissions import IsPartnerUser # <-- IMPORT OUR NEW PERMISSION
from django.db.models.functions import TruncMonth

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().order_by('price_ngn')
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

class PartnerSpaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PartnerSpace.objects.all()
    serializer_class = PartnerSpaceSerializer
    # Still IsAuthenticated (for subscribers to see the map)

class GenerateCheckInTokenView(generics.GenericAPIView):
    serializer_class = CheckInTokenSerializer
    permission_classes = [permissions.IsAuthenticated] # Correct (for subscribers)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()
        try:
            sub = user.subscription
            if not sub.is_active or (sub.end_date and sub.end_date < now.date()):
                return Response({"error": "Your subscription is not active."}, status=status.HTTP_403_FORBIDDEN)
        except Subscription.DoesNotExist:
            return Response({"error": "You do not have a subscription."}, status=status.HTTP_403_FORBIDDEN)
        
        start_date = sub.start_date
        days_used = CheckIn.objects.filter(user=user, timestamp__gte=start_date).count()
        total_days = sub.plan.included_days

        if days_used >= total_days:
            return Response({"error": "You have no check-in days left."}, status=status.HTTP_403_FORBIDDEN)

        CheckInToken.objects.filter(user=user).delete()
        token = CheckInToken.objects.create(user=user)
        serializer = self.get_serializer(token)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CheckInValidateView(generics.GenericAPIView):
    serializer_class = CheckInValidationSerializer
    
    # --- SECURITY UPGRADE ---
    permission_classes = [IsPartnerUser] # Now only partners can validate!

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        space_id = serializer.validated_data['space_id']
        now = timezone.now()

        # Check if the partner is trying to validate for THEIR OWN space
        if request.user.managed_space.id != space_id:
            return Response({"error": "You are not authorized to validate check-ins for this space."}, status=status.HTTP_403_FORBIDDEN)

        space = request.user.managed_space # We know it's their space

        try:
            token = CheckInToken.objects.select_related('user', 'user__subscription__plan').get(code=code)
        except CheckInToken.DoesNotExist:
            return Response({"error": "INVALID: Code not found."}, status=status.HTTP_404_NOT_FOUND)

        if token.expires_at < now:
            token.delete()
            return Response({"error": "INVALID: Code has expired."}, status=status.HTTP_410_GONE)

        user = token.user
        try:
            plan = user.subscription.plan
            if not user.subscription.is_active: raise Exception
        except Exception:
            return Response({"error": "INVALID: User has no active subscription."}, status=status.HTTP_403_FORBIDDEN)

        if space.access_tier == 'PREMIUM' and plan.access_tier == 'STANDARD':
            return Response({"error": "INVALID: User's plan does not allow access to this Premium space."}, status=status.HTTP_403_FORBIDDEN)

        CheckIn.objects.create(user=user, space=space)
        token.delete()
        
        user_serializer = UserProfileSerializer(user)
        return Response({"status": "VALID", "user": user_serializer.data}, status=status.HTTP_200_OK)

# --- NEW VIEW ---
class PartnerDashboardView(generics.RetrieveAPIView):
    """
    API endpoint for the partner's dashboard.
    GET /api/partner/dashboard/
    """
    permission_classes = [IsPartnerUser]

    def get(self, request, *args, **kwargs):
        partner_space = request.user.managed_space
        today = timezone.now().date()
        this_month = today.replace(day=1)

        # 1. "Current Members Checked-In"
        # For MVP, we'll count unique check-ins for today.
        current_members_count = CheckIn.objects.filter(
            space=partner_space,
            timestamp__date=today
        ).values('user').distinct().count()

        # 2. "Monthly Check-ins" (for the current calendar month)
        monthly_checkins_count = CheckIn.objects.filter(
            space=partner_space,
            timestamp__gte=this_month
        ).count()
        
        # 3. "Monthly Payout"
        payout_rate = partner_space.payout_per_checkin_ngn
        monthly_payout_ngn = monthly_checkins_count * payout_rate

        data = {
            "space_name": partner_space.name,
            "current_members_checked_in": current_members_count,
            "monthly_checkins": monthly_checkins_count,
            "payout_per_checkin_ngn": payout_rate,
            "monthly_payout_ngn": monthly_payout_ngn
        }
        return Response(data, status=status.HTTP_200_OK)
