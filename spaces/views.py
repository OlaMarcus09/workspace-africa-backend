from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
import requests
import traceback

from .models import Plan, PartnerSpace, CheckIn, CheckInToken, Subscription
from .serializers import (
    PlanSerializer, 
    PartnerSpaceSerializer, 
    CheckInTokenSerializer,
    CheckInValidationSerializer,
    CheckInReportSerializer
)
from users.serializers import TeamMemberSerializer 
from .permissions import IsPartnerUser

PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_BASE_URL = "https://api.paystack.co"

# Get the User model
User = get_user_model()

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().order_by('price_ngn')
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

class PartnerSpaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PartnerSpace.objects.all()
    serializer_class = PartnerSpaceSerializer

class GenerateCheckInTokenView(generics.GenericAPIView):
    """
    Handles the generation of a 6-digit access code for subscribers.
    """
    serializer_class = CheckInTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # 1. Validation: Ensure user is authenticated and not anonymous
        if not user or user.is_anonymous:
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        now = timezone.now()
        
        try:
            # 2. Validation: Check for an active subscription
            sub = user.subscriptions.filter(is_active=True).first()
            
            if not sub:
                return Response({"error": "No active subscription found."}, status=status.HTTP_403_FORBIDDEN)
            
            # 3. Validation: Check for expiry
            if sub.end_date and sub.end_date < now.date():
                sub.is_active = False
                sub.save()
                return Response({"error": "Subscription has expired."}, status=status.HTTP_403_FORBIDDEN)
                
        except Exception as e:
            return Response({"error": f"Authorization check failed: {str(e)}"}, status=status.HTTP_403_FORBIDDEN)

        # 4. Usage Tracking: Count distinct check-in days for the current plan cycle
        start_date = sub.start_date
        used_dates_qs = CheckIn.objects.filter(
            user=user, 
            timestamp__gte=start_date
        ).values_list('timestamp__date', flat=True)
        
        used_dates = set(used_dates_qs)
        days_used_count = len(used_dates)
        total_days_allowed = sub.plan.included_days

        today = now.date()
        is_already_checked_in_today = today in used_dates

        # 5. Plan Limits: Prevent new bookings if monthly limit reached
        if not is_already_checked_in_today:
            if days_used_count >= total_days_allowed:
                return Response({"error": "Monthly plan limit reached."}, status=status.HTTP_403_FORBIDDEN)

        # 6. Token Generation: Clear existing tokens and create a fresh one
        CheckInToken.objects.filter(user=user).delete()
        token = CheckInToken.objects.create(user=user)
        
        serializer = self.get_serializer(token)
        return Response({
            **serializer.data,
            "meta": {
                "plan": sub.plan.name,
                "days_used": days_used_count + (0 if is_already_checked_in_today else 1),
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

        if request.user.managed_space.id != space_id:
            return Response({"error": "Unauthorized space."}, status=status.HTTP_403_FORBIDDEN)
        
        space = request.user.managed_space
        try:
            token = CheckInToken.objects.select_related('user').get(code=code)
        except CheckInToken.DoesNotExist:
            return Response({"error": "Code not found."}, status=status.HTTP_404_NOT_FOUND)

        user = token.user
        CheckIn.objects.create(user=user, space=space)
        token.delete()

        user_serializer = TeamMemberSerializer(user) 
        return Response({"status": "VALID", "user": user_serializer.data}, status=status.HTTP_200_OK)

class PartnerDashboardView(generics.RetrieveAPIView):
    permission_classes = [IsPartnerUser]
    def get(self, request, *args, **kwargs):
        partner_space = request.user.managed_space
        today = timezone.now().date()
        current_members_count = CheckIn.objects.filter(space=partner_space, timestamp__date=today).values('user').distinct().count()
        data = {"space_name": partner_space.name, "current_members": current_members_count}
        return Response(data, status=status.HTTP_200_OK)

class PaymentInitializeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        plan_id = request.data.get('plan_id')
        
        if not plan_id:
            return Response({"error": "plan_id is required"}, status=400)
        
        plan = get_object_or_404(Plan, id=plan_id)
        callback_url = getattr(settings, 'PAYMENT_CALLBACK_URL', 'https://workspace-nomad.vercel.app/payment-success')
        
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "email": user.email,
            "amount": int(plan.price_ngn * 100),
            "callback_url": callback_url,
            "metadata": {
                "user_id": str(user.id),
                "plan_id": str(plan.id),
                "user_email": user.email,
                "plan_name": plan.name
            }
        }
        
        if plan.paystack_plan_code:
            data["plan"] = plan.paystack_plan_code
        
        try:
            response = requests.post(f"{PAYSTACK_BASE_URL}/transaction/initialize", headers=headers, json=data)
            response_data = response.json()
            if response_data.get('status'):
                return Response(response_data['data'], status=status.HTTP_200_OK)
            return Response({"error": response_data.get('message', 'Initialization failed')}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class PaymentVerifyView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        reference = request.query_params.get('reference')
        if not reference:
            return Response({"error": "No reference provided"}, status=400)

        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        
        try:
            resp = requests.get(f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=headers)
            resp_json = resp.json()
            
            if not resp_json.get('status') or resp_json['data']['status'] != 'success':
                return Response({"error": "Payment verification failed"}, status=400)

            data = resp_json['data']
            metadata = data.get('metadata', {})
            
            # Identify Plan
            plan_id = metadata.get('plan_id') if isinstance(metadata, dict) else None
            plan = None

            if plan_id:
                plan = Plan.objects.filter(id=plan_id).first()
            
            if not plan:
                plan_info = data.get('plan')
                plan_code = plan_info.get('plan_code') if isinstance(plan_info, dict) else plan_info
                if plan_code:
                    plan = Plan.objects.filter(paystack_plan_code=plan_code).first()

            if not plan:
                return Response({"error": "Could not identify plan for this transaction"}, status=400)

            # Identify User
            user_email = data['customer']['email']
            user = User.objects.filter(email=user_email).first()
            if not user:
                return Response({"error": "User associated with payment not found"}, status=404)

            # Prevent Duplicate Processing
            if Subscription.objects.filter(paystack_reference=reference).exists():
                return Response({"status": "success", "message": "Transaction already processed"}, status=200)

            # Activate New Subscription
            user.subscriptions.filter(is_active=True).update(is_active=False)

            Subscription.objects.create(
                user=user, 
                plan=plan, 
                paystack_reference=reference, 
                is_active=True,
                start_date=timezone.now().date()
            )
            
            return Response({
                "status": "success", 
                "message": "Subscription activated successfully",
                "plan": plan.name
            }, status=200)

        except Exception as e:
            print(traceback.format_exc())
            return Response({"error": "Internal Processing Error", "details": str(e)}, status=500)

class PartnerReportView(generics.ListAPIView):
    serializer_class = CheckInReportSerializer
    permission_classes = [IsPartnerUser]
    def get_queryset(self):
        return CheckIn.objects.filter(space=self.request.user.managed_space).order_by('-timestamp')