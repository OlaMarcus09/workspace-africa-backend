from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from .models import Plan, PartnerSpace, CheckIn, CheckInToken, Subscription
from .serializers import (
    PlanSerializer, 
    PartnerSpaceSerializer, 
    CheckInTokenSerializer,
    CheckInValidationSerializer,
    SubscriptionCreateSerializer # <-- Import new
)
from users.serializers import UserProfileSerializer 
from django.utils import timezone
from django.db import transaction
from .permissions import IsPartnerUser

# ... (PlanViewSet and PartnerSpaceViewSet are unchanged) ...
class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().order_by('price_ngn')
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

class PartnerSpaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PartnerSpace.objects.all()
    serializer_class = PartnerSpaceSerializer

class GenerateCheckInTokenView(generics.GenericAPIView):
    # ... (This view is unchanged) ...
    serializer_class = CheckInTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()
        try:
            sub = user.subscriptions.first() # Use .subscriptions.first()
            if not sub or not sub.is_active or (sub.end_date and sub.end_date < now.date()):
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
    # ... (This view is unchanged) ...
    serializer_class = CheckInValidationSerializer
    permission_classes = [IsPartnerUser]
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']
        space_id = serializer.validated_data['space_id']
        now = timezone.now()
        if request.user.managed_space.id != space_id:
            return Response({"error": "You are not authorized for this space."}, status=status.HTTP_403_FORBIDDEN)
        space = request.user.managed_space
        try:
            token = CheckInToken.objects.select_related('user', 'user__subscriptions__plan').get(code=code)
        except CheckInToken.DoesNotExist:
            return Response({"error": "INVALID: Code not found."}, status=status.HTTP_404_NOT_FOUND)
        if token.expires_at < now:
            token.delete()
            return Response({"error": "INVALID: Code has expired."}, status=status.HTTP_410_GONE)
        user = token.user
        try:
            plan = user.subscriptions.first().plan # Use .subscriptions.first()
            if not user.subscriptions.first().is_active: raise Exception
        except Exception:
            return Response({"error": "INVALID: User has no active subscription."}, status=status.HTTP_403_FORBIDDEN)
        if space.access_tier == 'PREMIUM' and plan.access_tier == 'STANDARD':
            return Response({"error": "INVALID: User's plan does not allow access to this Premium space."}, status=status.HTTP_403_FORBIDDEN)
        CheckIn.objects.create(user=user, space=space)
        token.delete()
        user_serializer = UserProfileSerializer(user)
        return Response({"status": "VALID", "user": user_serializer.data}, status=status.HTTP_200_OK)

class PartnerDashboardView(generics.RetrieveAPIView):
    # ... (This view is unchanged) ...
    permission_classes = [IsPartnerUser]
    def get(self, request, *args, **kwargs):
        partner_space = request.user.managed_space
        today = timezone.now().date()
        this_month = today.replace(day=1)
        current_members_count = CheckIn.objects.filter(space=partner_space, timestamp__date=today).values('user').distinct().count()
        monthly_checkins_count = CheckIn.objects.filter(space=partner_space, timestamp__gte=this_month).count()
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

# --- NEW VIEW ---
class SubscriptionCreateView(generics.CreateAPIView):
    """
    Endpoint for creating a subscription after a successful
    Paystack payment.
    POST /api/subscriptions/create/
    """
    serializer_class = SubscriptionCreateSerializer
    permission_classes = [permissions.IsAuthenticated] # Only a logged-in user can create a sub

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        user = request.user
        plan = Plan.objects.get(id=data['plan_id'])
        
        # TODO: Here, we should contact Paystack with our SECRET_KEY
        # to verify the 'paystack_reference' is real and successful.
        # For MVP, we will trust the client.
        
        # Deactivate any old subscriptions
        user.subscriptions.update(is_active=False)
        
        # Create the new, active subscription
        new_sub = Subscription.objects.create(
            user=user,
            plan=plan,
            paystack_reference=data['paystack_reference'],
            is_active=True
            # We'll add 'end_date' logic later with webhooks
        )
        
        return Response(SubscriptionSerializer(new_sub).data, status=status.HTTP_201_CREATED)
