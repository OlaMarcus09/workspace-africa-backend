from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
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

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().order_by('price_ngn')
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

class PartnerSpaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PartnerSpace.objects.all()
    serializer_class = PartnerSpaceSerializer

class GenerateCheckInTokenView(generics.GenericAPIView):
    serializer_class = CheckInTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()
        try:
            sub = user.subscriptions.filter(is_active=True).first()
            if not sub:
                return Response({"error": "No active subscription."}, status=status.HTTP_403_FORBIDDEN)
            if sub.end_date and sub.end_date < now.date():
                sub.is_active = False
                sub.save()
                return Response({"error": "Subscription expired."}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response({"error": "Auth check failed."}, status=status.HTTP_403_FORBIDDEN)

        start_date = sub.start_date
        used_dates_qs = CheckIn.objects.filter(user=user, timestamp__gte=start_date).values_list('timestamp__date', flat=True)
        used_dates = set(used_dates_qs)
        days_used_count = len(used_dates)
        total_days_allowed = sub.plan.included_days

        today = now.date()
        is_new_day_visit = today not in used_dates

        if is_new_day_visit:
            if days_used_count >= total_days_allowed:
                return Response({"error": "Plan limit reached."}, status=status.HTTP_403_FORBIDDEN)

        CheckInToken.objects.filter(user=user).delete()
        token = CheckInToken.objects.create(user=user)
        
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
        plan = get_object_or_404(Plan, id=plan_id)
        callback_url = getattr(settings, 'PAYMENT_CALLBACK_URL', 'https://workspace-nomad.vercel.app/payment-success')
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}","Content-Type": "application/json"}
        data = {
            "email": user.email,
            "amount": int(plan.price_ngn * 100),
            "plan": plan.paystack_plan_code,
            "callback_url": callback_url,
            "metadata": {"user_id": user.id, "plan_id": plan.id}
        }
        try:
            response = requests.post(f"{PAYSTACK_BASE_URL}/transaction/initialize", headers=headers, json=data)
            return Response(response.json()['data'], status=status.HTTP_200_OK)
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
            # 1. Fetch from Paystack
            resp = requests.get(f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=headers)
            resp_json = resp.json()
            
            if not resp_json.get('status') or resp_json['data']['status'] != 'success':
                return Response({"error": "Paystack says payment failed or is incomplete."}, status=400)

            data = resp_json['data']
            
            # 2. Extract Plan Code safely
            plan_code = None
            if 'plan' in data and data['plan']:
                if isinstance(data['plan'], dict):
                    plan_code = data['plan'].get('plan_code') or data['plan'].get('code')
                else:
                    plan_code = data['plan']
            
            # Fallback to metadata
            if not plan_code and 'metadata' in data:
                 if isinstance(data['metadata'], dict):
                     plan_id = data['metadata'].get('plan_id')
                     if plan_id:
                         plan_obj = Plan.objects.get(id=plan_id)
                         plan_code = plan_obj.paystack_plan_code

            if not plan_code:
                return Response({"error": "Could not identify Plan Code from transaction data."}, status=400)

            # 3. Create Subscription
            user_email = data['customer']['email']
            user = get_object_or_404(settings.AUTH_USER_MODEL, email=user_email)
            plan = get_object_or_404(Plan, paystack_plan_code=plan_code)

            if Subscription.objects.filter(paystack_reference=reference).exists():
                return Response({"error": "Transaction already processed"}, status=400)

            # Deactivate old ones
            user.subscriptions.update(is_active=False)

            # Create new one
            Subscription.objects.create(
                user=user, 
                plan=plan, 
                paystack_reference=reference, 
                is_active=True,
                start_date=timezone.now().date()
            )

            # --- CHANGE: Instead of redirect(), return JSON ---
            # This prevents the 500 error caused by Axios trying to follow a redirect
            return Response({
                "status": "success", 
                "message": "Subscription activated successfully"
            }, status=200)

        except Exception as e:
            # Send the real error back to the frontend alert
            error_trace = traceback.format_exc()
            print(error_trace)
            return Response({
                "error": "Internal Processing Error",
                "message": str(e),
                "trace": error_trace
            }, status=500)

class PartnerReportView(generics.ListAPIView):
    serializer_class = CheckInReportSerializer
    permission_classes = [IsPartnerUser]
    def get_queryset(self):
        return CheckIn.objects.filter(space=self.request.user.managed_space).order_by('-timestamp')