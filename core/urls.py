from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),

    # Auth
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # <-- FIXED

    # Users
    path('api/users/', include('users.urls')),

    # Spaces & Partners
    path('api/', include('spaces.urls')), 
    
    # Team Admin Portal
    path('api/team/', include('teams.urls')),
]
