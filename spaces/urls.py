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
    PartnerReportView # <-- Import new
)

router = DefaultRouter()
router.register(r'plans', PlanViewSet)
router.register(r'spaces', PartnerSpaceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Subscriber endpoints
    path('check-in/generate/', GenerateCheckInTokenView.as_view(), name='generate_check_in_token'),
    path('payments/initialize/', PaymentInitializeView.as_view(), name='payment_initialize'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment_verify'),
    
    # Partner-only endpoints
    path('check-in/validate/', CheckInValidateView.as_view(), name='validate_check_in_token'),
    path('partner/dashboard/', PartnerDashboardView.as_view(), name='partner_dashboard'),
    path('partner/reports/', PartnerReportView.as_view(), name='partner_reports'), # <-- NEW
]

from .analytics_views import UserAnalyticsView

# Add to urlpatterns:
path('analytics/', UserAnalyticsView.as_view(), name='user_analytics'),


from .analytics_views import UserAnalyticsView

# Add to urlpatterns:
path('analytics/', UserAnalyticsView.as_view(), name='user_analytics'),


from .analytics_views import UserAnalyticsView

urlpatterns += [
    path('analytics/', UserAnalyticsView.as_view(), name='user_analytics'),
]

