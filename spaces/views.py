from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
import requests # We need this to talk to Paystack

from .models import Plan, PartnerSpace, CheckIn, CheckInToken, Subscription
from .serializers import (
    PlanSerializer, 
    PartnerSpaceSerializer, 
    CheckInTokenSerializer,
    CheckInValidationSerializer,
    SubscriptionSerializer # We'll use this
)
from users.serializers import UserProfileSerializer 
from .permissions import IsPartnerUser

# --- Paystack API Settings ---
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_BASE_URL = "https://api.paystack.co"

# --- 1. Plan & Space Views (Unchanged) ---
class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().order_by('price_ngn')
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

class PartnerSpaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PartnerSpace.objects.all()
    serializer_class = PartnerSpaceSerializer

# --- 2. Check-In & Partner Views (Unchanged) ---
class GenerateCheckInTokenView(generics.GenericAPIView):
    serializer_class = CheckInTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()
        try:
            sub = user.subscriptions.first()
            if not sub or not sub.is_active or (sub.end_date and sub.end_date < now.date()):
                return Response({"error": "Your subscription is not active."}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
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
            plan = user.subscriptions.first().plan
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

# --- 3. NEW PAYMENT ENDPOINTS ---

class PaymentInitializeView(generics.GenericAPIView):
    """
    Endpoint for initializing a new subscription payment.
    POST /api/payments/initialize/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        plan_id = request.data.get('plan_id')
        plan = get_object_or_404(Plan, id=plan_id)
        
        # We need to get the frontend URL from our settings
        callback_url = settings.PAYMENT_CALLBACK_URL

        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        
        # Paystack data: we use the Plan Code
        data = {
            "email": user.email,
            "plan": plan.paystack_plan_code,
            "callback_url": callback_url,
        }

        try:
            # Call Paystack to create a transaction
            response = requests.post(
                f"{PAYSTACK_BASE_URL}/transaction/initialize",
                headers=headers,
                json=data
            )
            response.raise_for_status() # Raise an error for bad responses
            
            # The response has our payment link
            paystack_data = response.json()
            return Response(paystack_data['data'], status=status.HTTP_200_OK)
            
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Payment gateway error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentVerifyView(generics.GenericAPIView):
    """
    Endpoint that Paystack redirects back to.
    GET /api/payments/verify/?reference=...
    """
    permission_classes = [permissions.AllowAny] # Must be public for Paystack to call

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        reference = request.query_params.get('reference')
        if not reference:
            return Response({"error": "No reference provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Verify the transaction with Paystack
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        try:
            response = requests.get(
                f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()['data']

            if data['status'] != 'success':
                return Response({"error": "Payment not successful"}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Get the user and plan
            user_email = data['customer']['email']
            plan_code = data['plan']
            
            user = get_object_or_404(settings.AUTH_USER_MODEL, email=user_email)
            plan = get_object_or_404(Plan, paystack_plan_code=plan_code)

            # 3. Check if this payment has already been processed
            if Subscription.objects.filter(paystack_reference=reference).exists():
                return Response({"error": "This payment has already been processed."}, status=status.HTTP_400_BAD_REQUEST)

            # 4. Create the subscription
            user.subscriptions.update(is_active=False) # Deactivate old ones
            Subscription.objects.create(
                user=user,
                plan=plan,
                paystack_reference=reference,
                is_active=True
            )
            
            # 5. Redirect the user back to the app's success page
            # We'll set this in Render
            success_url = settings.PAYMENT_SUCCESS_URL
            return redirect(success_url)

        except requests.exceptions.RequestException as e:
            return Response({"error": f"Payment verification error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
