from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlanViewSet, 
    PartnerSpaceViewSet, 
    GenerateCheckInTokenView,
    CheckInValidateView,
    PartnerDashboardView,
    PaymentInitializeView, # <-- NEW
    PaymentVerifyView      # <-- NEW
)

router = DefaultRouter()
router.register(r'plans', PlanViewSet)
router.register(r'spaces', PartnerSpaceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Subscriber endpoints
    path('check-in/generate/', GenerateCheckInTokenView.as_view(), name='generate_check_in_token'),
    
    # --- NEW PAYMENT FLOW ---
    path('payments/initialize/', PaymentInitializeView.as_view(), name='payment_initialize'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment_verify'),
    
    # Partner-only endpoints
    path('check-in/validate/', CheckInValidateView.as_view(), name='validate_check_in_token'),
    path('partner/dashboard/', PartnerDashboardView.as_view(), name='partner_dashboard'),
]
