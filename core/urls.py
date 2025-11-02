from django.contrib import admin
from django.urls import path, include # Import 'include'
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- FIX: DRF Login/Logout (for Browsable API) ---
    # This is the line we were missing. It adds the "Log in" link.
    path('api-auth/', include('rest_framework.urls')),

    # --- Our Auth API (for tokens) ---
    # POST /api/auth/token/
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- Our User Management API ---
    # POST /api/users/register/
    # GET  /api/users/me/
    path('api/users/', include('users.urls')),

    # --- Our Spaces & Plans API ---
    # GET /api/plans/
    # GET /api/spaces/
    # POST /api/check-in/generate/
    # POST /api/check-in/validate/
    path('api/', include('spaces.urls')), 
]
