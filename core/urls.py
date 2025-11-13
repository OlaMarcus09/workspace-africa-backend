from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import MyTokenObtainPairView # Import our custom view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),

    # Auth
    path('api/auth/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Users
    path('api/users/', include('users.urls')),

    # Spaces & Partners
    path('api/', include('spaces.urls')), 
    
    # Team Admin Portal
    path('api/team/', include('teams.urls')),
]

from django.db import connection
from django.http import JsonResponse

def debug_db(request):
    with connection.cursor() as cursor:
        # Check if paystack_reference column exists
        try:
            if connection.vendor == 'postgresql':
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='spaces_subscription' AND column_name='paystack_reference';")
            else:  # sqlite
                cursor.execute("PRAGMA table_info(spaces_subscription);")
            
            columns = [row[0] if connection.vendor == 'postgresql' else row[1] for row in cursor.fetchall()]
            
            return JsonResponse({
                'database_vendor': connection.vendor,
                'paystack_reference_exists': 'paystack_reference' in columns,
                'all_columns': columns,
                'migration_applied': '0009_subscription_paystack_reference' in str(columns)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)})

urlpatterns += [
    path('debug-db/', debug_db, name='debug_db'),
]

from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy", "message": "API is working"})

urlpatterns += [
    path('health/', health_check, name='health_check'),
]
