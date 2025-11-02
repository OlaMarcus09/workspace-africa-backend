from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeamAdminDashboardView, TeamMemberViewSet, InvitationViewSet

router = DefaultRouter()
router.register(r'members', TeamMemberViewSet, basename='team-member')
router.register(r'invites', InvitationViewSet, basename='team-invitation')

urlpatterns = [
    # Main dashboard view
    path('dashboard/', TeamAdminDashboardView.as_view(), name='team-dashboard'),
    
    # Router URLs for /api/team/members/ and /api/team/invites/
    path('', include(router.urls)),
]
