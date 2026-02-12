from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlanViewSet, 
    PartnerSpaceViewSet, 
    GenerateCheckInTokenView,
    CheckInValidateView,
    PartnerDashboardView,
    PaymentInitializeView,
    PaymentVerifyView,
    PartnerReportView
)
from .analytics_views import UserAnalyticsView
from .partner_application import PartnerApplicationView

router = DefaultRouter()
router.register(r'plans', PlanViewSet)
router.register(r'spaces', PartnerSpaceViewSet)

urlpatterns = [
    # 1. SPECIFIC PATHS FIRST (Prevents 405 Method Not Allowed)
    # This must match your frontend call exactly: /api/spaces/generate-token/
    path('spaces/generate-token/', GenerateCheckInTokenView.as_view(), name='generate_token'),
    
    # 2. Subscriber & Payment endpoints
    path('payments/initialize/', PaymentInitializeView.as_view(), name='payment_initialize'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment_verify'),
    
    # 3. Partner & Analytics endpoints
    path('check-in/validate/', CheckInValidateView.as_view(), name='validate_check_in_token'),
    path('partner/dashboard/', PartnerDashboardView.as_view(), name='partner_dashboard'),
    path('partner/reports/', PartnerReportView.as_view(), name='partner_reports'),
    path('partner/apply/', PartnerApplicationView.as_view(), name='partner_apply'),
    path('analytics/', UserAnalyticsView.as_view(), name='user_analytics'),

    # 4. ROUTER LAST
    path('', include(router.urls)),
]