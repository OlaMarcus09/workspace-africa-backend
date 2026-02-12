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
        
        if not plan_id:
            return Response({"error": "plan_id is required"}, status=400)
        
        plan = get_object_or_404(Plan, id=plan_id)
        callback_url = getattr(settings, 'PAYMENT_CALLBACK_URL', 'https://workspace-nomad.vercel.app/payment-success')
        
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        # IMPORTANT: Send metadata as strings for better compatibility
        data = {
            "email": user.email,
            "amount": int(plan.price_ngn * 100),  # Convert to kobo
            "callback_url": callback_url,
            "metadata": {
                "user_id": str(user.id),      # Convert to string
                "plan_id": str(plan.id),      # Convert to string
                "user_email": user.email,     # Backup
                "plan_name": plan.name        # For debugging
            }
        }
        
        # Only add plan code if it exists (for subscription plans)
        if plan.paystack_plan_code:
            data["plan"] = plan.paystack_plan_code
        
        print(f"Initializing payment for user {user.email}, plan {plan.name}")
        print(f"Sending to Paystack: {data}")
        
        try:
            response = requests.post(
                f"{PAYSTACK_BASE_URL}/transaction/initialize", 
                headers=headers, 
                json=data
            )
            response_data = response.json()
            
            if response_data.get('status'):
                print(f"Payment initialized successfully: {response_data['data'].get('reference')}")
                return Response(response_data['data'], status=status.HTTP_200_OK)
            else:
                print(f"Paystack error: {response_data}")
                return Response({
                    "error": "Payment initialization failed",
                    "details": response_data.get('message', 'Unknown error')
                }, status=400)
                
        except Exception as e:
            print(f"Exception during payment init: {str(e)}")
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
            
            # Log the full response for debugging
            print(f"=== PAYSTACK RESPONSE ===")
            print(f"Full response: {resp_json}")
            
            if not resp_json.get('status') or resp_json['data']['status'] != 'success':
                return Response({
                    "error": "Paystack says payment failed or is incomplete.",
                    "details": resp_json.get('message', 'Unknown error')
                }, status=400)

            data = resp_json['data']
            
            # 2. FIXED: Get plan_id from metadata FIRST (most reliable)
            plan = None
            plan_id = None
            
            # Try to get plan_id from metadata
            if 'metadata' in data and data['metadata']:
                if isinstance(data['metadata'], dict):
                    plan_id = data['metadata'].get('plan_id')
                    print(f"Found plan_id in metadata: {plan_id}")
            
            # If we have plan_id from metadata, use it directly
            if plan_id:
                try:
                    plan = Plan.objects.get(id=plan_id)
                    print(f"Successfully found plan: {plan.name} (ID: {plan.id})")
                except Plan.DoesNotExist:
                    print(f"ERROR: Plan with ID {plan_id} not found in database")
                    return Response({
                        "error": f"Plan with ID {plan_id} not found in database"
                    }, status=400)
            else:
                # Fallback: Try to extract plan code from Paystack response
                plan_code = None
                if 'plan' in data and data['plan']:
                    if isinstance(data['plan'], dict):
                        plan_code = data['plan'].get('plan_code') or data['plan'].get('code')
                    elif isinstance(data['plan'], str):
                        plan_code = data['plan']
                
                print(f"Extracted plan_code from Paystack: {plan_code}")
                
                if plan_code:
                    try:
                        plan = Plan.objects.get(paystack_plan_code=plan_code)
                        print(f"Found plan by code: {plan.name}")
                    except Plan.DoesNotExist:
                        # List all available plans for debugging
                        all_plans = list(Plan.objects.all().values('id', 'name', 'paystack_plan_code'))
                        print(f"Available plans in database: {all_plans}")
                        return Response({
                            "error": f"Plan with code '{plan_code}' not found in database",
                            "available_plans": all_plans
                        }, status=400)
                else:
                    print("ERROR: Could not extract plan information from transaction")
                    return Response({
                        "error": "Could not identify Plan from transaction data. No plan_id in metadata and no plan code in response."
                    }, status=400)

            # 3. Get user by email
            user_email = data['customer']['email']
            print(f"Looking for user with email: {user_email}")
            
            try:
                user = get_object_or_404(settings.AUTH_USER_MODEL, email=user_email)
                print(f"Found user: {user.id} - {user.email}")
            except Exception as e:
                print(f"ERROR: User not found: {str(e)}")
                return Response({
                    "error": f"User with email {user_email} not found"
                }, status=404)

            # 4. Check if already processed
            if Subscription.objects.filter(paystack_reference=reference).exists():
                print(f"WARNING: Transaction {reference} already processed")
                return Response({
                    "error": "Transaction already processed",
                    "message": "This payment has already been recorded"
                }, status=400)

            # 5. Deactivate old subscriptions
            old_subs_count = user.subscriptions.filter(is_active=True).update(is_active=False)
            print(f"Deactivated {old_subs_count} old subscriptions")

            # 6. Create new subscription
            subscription = Subscription.objects.create(
                user=user, 
                plan=plan, 
                paystack_reference=reference, 
                is_active=True,
                start_date=timezone.now().date()
            )
            
            print(f"SUCCESS: Created subscription {subscription.id} for user {user.email}")
            print(f"Plan: {plan.name}, Reference: {reference}")

            return Response({
                "status": "success", 
                "message": "Subscription activated successfully",
                "subscription": {
                    "plan": plan.name,
                    "reference": reference,
                    "start_date": subscription.start_date.isoformat()
                }
            }, status=200)

        except Exception as e:
            error_trace = traceback.format_exc()
            print("=== CRITICAL ERROR ===")
            print(f"Error: {str(e)}")
            print(error_trace)
            print("======================")
            
            return Response({
                "error": "Internal Processing Error",
                "message": str(e),
                "reference": reference,
                "hint": "Check server logs for full traceback"
            }, status=500)

class PartnerReportView(generics.ListAPIView):
    serializer_class = CheckInReportSerializer
    permission_classes = [IsPartnerUser]
    def get_queryset(self):
        return CheckIn.objects.filter(space=self.request.user.managed_space).order_by('-timestamp')