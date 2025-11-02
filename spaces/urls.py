from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlanViewSet, 
    PartnerSpaceViewSet, 
    GenerateCheckInTokenView,
    CheckInValidateView,
    PartnerDashboardView # <-- Import new
)

router = DefaultRouter()
router.register(r'plans', PlanViewSet)
router.register(r'spaces', PartnerSpaceViewSet)

urlpatterns = [
    # Public & Subscriber endpoints
    path('', include(router.urls)),
    path('check-in/generate/', GenerateCheckInTokenView.as_view(), name='generate_check_in_token'),
    
    # Partner-only endpoints
    path('check-in/validate/', CheckInValidateView.as_view(), name='validate_check_in_token'),
    path('partner/dashboard/', PartnerDashboardView.as_view(), name='partner_dashboard'), # <-- NEW URL
]
