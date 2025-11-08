from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlanViewSet, 
    PartnerSpaceViewSet, 
    GenerateCheckInTokenView,
    CheckInValidateView,
    PartnerDashboardView,
    SubscriptionCreateView # <-- Import new
)

router = DefaultRouter()
router.register(r'plans', PlanViewSet)
router.register(r'spaces', PartnerSpaceViewSet)

urlpatterns = [
    # Router URLs (e.g., /api/plans/, /api/spaces/)
    path('', include(router.urls)),
    
    # Subscriber endpoints
    path('check-in/generate/', GenerateCheckInTokenView.as_view(), name='generate_check_in_token'),
    path('subscriptions/create/', SubscriptionCreateView.as_view(), name='subscription_create'), # <-- NEW
    
    # Partner-only endpoints
    path('check-in/validate/', CheckInValidateView.as_view(), name='validate_check_in_token'),
    path('partner/dashboard/', PartnerDashboardView.as_view(), name='partner_dashboard'),
]
