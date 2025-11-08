from django.contrib import admin
from django.urls import path, include
# We don't need the default view anymore
from rest_framework_simplejwt.views import TokenRefreshView
# We import our new view
from users.views import MyTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),

    # Auth
    # --- THIS IS THE FIX ---
    # We are now using our custom view, not the default one
    path('api/auth/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Users
    path('api/users/', include('users.urls')),

    # Spaces & Partners
    path('api/', include('spaces.urls')), 
    
    # Team Admin Portal
    path('api/team/', include('teams.urls')),
]
