from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
import requests

from .models import Plan, PartnerSpace, CheckIn, CheckInToken, Subscription
from .serializers import (
    PlanSerializer, 
    PartnerSpaceSerializer, 
    CheckInTokenSerializer,
    CheckInValidationSerializer,
    SubscriptionSerializer,
    SubscriptionCreateSerializer,
    CheckInReportSerializer
)
from users.serializers import TeamMemberSerializer 
from .permissions import IsPartnerUser

PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_BASE_URL = "https://api.paystack.co"

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().order_by('price_ngn')
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

class PartnerSpaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PartnerSpace.objects.all()
    serializer_class = PartnerSpaceSerializer

class GenerateCheckInTokenView(generics.GenericAPIView):
    """
    THE GATEKEEPER: Checks if user has a valid subscription and days remaining.
    """
    serializer_class = CheckInTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()

        # 1. Check for Active Subscription
        try:
            sub = user.subscriptions.filter(is_active=True).first()
            if not sub:
                return Response({"error": "You do not have an active subscription."}, status=status.HTTP_403_FORBIDDEN)
            
            # Check Expiration Date
            if sub.end_date and sub.end_date < now.date():
                sub.is_active = False
                sub.save()
                return Response({"error": "Your subscription has expired."}, status=status.HTTP_403_FORBIDDEN)
                
        except Exception:
            return Response({"error": "Subscription check failed."}, status=status.HTTP_403_FORBIDDEN)

        # 2. Count Days Used (The Smart Way)
        start_date = sub.start_date
        
        # Get a list of all unique dates the user has checked in
        used_dates_qs = CheckIn.objects.filter(
            user=user, 
            timestamp__gte=start_date
        ).values_list('timestamp__date', flat=True)
        
        # Convert to a set to ensure uniqueness (just in case DB distinct fails)
        used_dates = set(used_dates_qs)
        days_used_count = len(used_dates)
        total_days_allowed = sub.plan.included_days

        # 3. The Logic Check
        # If today is ALREADY in the used_dates, it means they checked in earlier today.
        # We allow them to generate another token (re-entry) without burning a new day.
        today = now.date()
        is_new_day_visit = today not in used_dates

        if is_new_day_visit:
            # If it's a new day, we must check if they have days remaining
            if days_used_count >= total_days_allowed:
                return Response({
                    "error": f"You have used all {total_days_allowed} days in your plan. Upgrade to Flex Pro/Unlimited."
                }, status=status.HTTP_403_FORBIDDEN)

        # 4. Generate Token
        CheckInToken.objects.filter(user=user).delete() # Cleanup old tokens
        token = CheckInToken.objects.create(user=user)
        
        # Return success with remaining days info
        remaining = total_days_allowed - days_used_count
        # Adjust display logic: if it's a new day visit, they are about to use one.
        if is_new_day_visit:
            remaining -= 1
            
        serializer = self.get_serializer(token)
        return Response({
            **serializer.data,
            "meta": {
                "plan": sub.plan.name,
                "days_used": days_used_count + (1 if is_new_day_visit else 0),
                "days_total": total_days_allowed
            }
        }, status=status.HTTP_201_CREATED)

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

        # 1. Partner Verification
        if request.user.managed_space.id != space_id:
            return Response({"error": "You are not authorized for this space."}, status=status.HTTP_403_FORBIDDEN)
        
        space = request.user.managed_space

        # 2. Token Verification
        try:
            token = CheckInToken.objects.select_related('user', 'user__subscriptions__plan').get(code=code)
        except CheckInToken.DoesNotExist:
            return Response({"error": "INVALID: Code not found."}, status=status.HTTP_404_NOT_FOUND)

        if token.expires_at < now:
            token.delete()
            return Response({"error": "INVALID: Code has expired."}, status=status.HTTP_410_GONE)

        user = token.user

        # 3. Double Check Subscription (In case it expired 2 mins ago)
        try:
            sub = user.subscriptions.filter(is_active=True).first()
            if not sub: raise Exception
            plan = sub.plan
        except Exception:
            return Response({"error": "INVALID: User has no active subscription."}, status=status.HTTP_403_FORBIDDEN)

        # 4. Access Tier Check
        if space.access_tier == 'PREMIUM' and plan.access_tier == 'STANDARD':
            return Response({"error": "INVALID: User's plan does not allow access to this Premium space."}, status=status.HTTP_403_FORBIDDEN)

        # 5. Record Check-In
        CheckIn.objects.create(user=user, space=space)
        token.delete()

        user_serializer = TeamMemberSerializer(user) 
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

class PaymentInitializeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        plan_id = request.data.get('plan_id')
        plan = get_object_or_404(Plan, id=plan_id)
        
        # Fallback if setting is missing
        callback_url = getattr(settings, 'PAYMENT_CALLBACK_URL', 'https://workspace-nomad.vercel.app/payment-success')
        
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": user.email,
            "amount": int(plan.price_ngn * 100), # Ensure amount is in kobo
            "plan": plan.paystack_plan_code,
            "callback_url": callback_url,
            "metadata": {
                "user_id": user.id,
                "plan_id": plan.id
            }
        }
        
        try:
            response = requests.post(f"{PAYSTACK_BASE_URL}/transaction/initialize", headers=headers, json=data)
            response.raise_for_status()
            paystack_data = response.json()
            return Response(paystack_data['data'], status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Payment gateway error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentVerifyView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        reference = request.query_params.get('reference')
        if not reference:
            return Response({"error": "No reference provided"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        
        try:
            response = requests.get(f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=headers)
            response.raise_for_status()
            data = response.json()['data']

            if data['status'] != 'success':
                return Response({"error": "Payment not successful"}, status=status.HTTP_400_BAD_REQUEST)

            # --- CRITICAL FIX START: Extract Plan Code Safely ---
            plan_code = None
            if 'plan' in data and data['plan']:
                # Paystack sometimes returns an object {code: "PLN_...", ...} or just a string
                if isinstance(data['plan'], dict):
                    plan_code = data['plan'].get('plan_code') or data['plan'].get('code')
                else:
                    plan_code = data['plan']
            
            # Fallback: check metadata if plan_code is still None
            if not plan_code and 'metadata' in data:
                 if isinstance(data['metadata'], dict):
                     plan_id = data['metadata'].get('plan_id')
                     if plan_id:
                         plan_obj = get_object_or_404(Plan, id=plan_id)
                         plan_code = plan_obj.paystack_plan_code

            if not plan_code:
                # Log detailed data to Vercel logs so we can debug if it fails again
                print(f"PAYSTACK ERROR: No plan code found. Data keys: {data.keys()}")
                if 'plan' in data: print(f"Plan Data: {data['plan']}")
                return Response({"error": "Could not identify plan from transaction"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Now we are safe to lookup
            user_email = data['customer']['email']
            user = get_object_or_404(settings.AUTH_USER_MODEL, email=user_email)
            plan = get_object_or_404(Plan, paystack_plan_code=plan_code)
            # --- CRITICAL FIX END ---

            if Subscription.objects.filter(paystack_reference=reference).exists():
                return Response({"error": "This payment has already been processed."}, status=status.HTTP_400_BAD_REQUEST)

            # Deactivate old subscriptions
            user.subscriptions.update(is_active=False)

            # Create NEW Connection
            Subscription.objects.create(
                user=user, 
                plan=plan, 
                paystack_reference=reference, 
                is_active=True
                # end_date is auto-calculated by DB triggers or logic elsewhere
            )

            success_url = getattr(settings, 'PAYMENT_SUCCESS_URL', 'https://workspace-nomad.vercel.app/payment-success')
            return redirect(success_url)

        except requests.exceptions.RequestException as e:
            return Response({"error": f"Payment verification error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PartnerReportView(generics.ListAPIView):
    serializer_class = CheckInReportSerializer
    permission_classes = [IsPartnerUser]
    
    def get_queryset(self):
        partner_space = self.request.user.managed_space
        return CheckIn.objects.filter(space=partner_space).order_by('-timestamp')