from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeamAdminDashboardView, 
    TeamMemberViewSet, 
    InvitationViewSet,
    TeamBillingView # <-- Import new
)

router = DefaultRouter()
router.register(r'members', TeamMemberViewSet, basename='team-member')
router.register(r'invites', InvitationViewSet, basename='team-invitation')

urlpatterns = [
    path('dashboard/', TeamAdminDashboardView.as_view(), name='team-dashboard'),
    path('billing/', TeamBillingView.as_view(), name='team-billing'), # <-- NEW URL
    
    path('', include(router.urls)),
]

from .add_subscription import add_subscription_to_team

urlpatterns += [
    path('add-subscription/', add_subscription_to_team, name='add-subscription'),
]
