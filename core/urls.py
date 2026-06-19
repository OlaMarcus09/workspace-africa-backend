from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import MyTokenObtainPairView
from django.db import connection
from django.http import JsonResponse
from django.core.management import call_command
from django.contrib.auth import get_user_model # Added for superuser creation


def create_admin(request):
    secret = request.GET.get("secret")
    if secret != "workspace2026admin":
        return JsonResponse({"error": "forbidden"}, status=403)

    User = get_user_model()
    email = "olawalemarcus92@gmail.com"

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": "olawale",
            "is_staff": True,
            "is_superuser": True,
        }
    )

    if created:
        user.set_password("WorkspaceAfrica2026!")
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return JsonResponse({"status": "created", "email": email})

    user.is_staff = True
    user.is_superuser = True
    user.save()
    return JsonResponse({"status": "already_exists", "email": email})


def run_migrations(request):
    secret = request.GET.get('secret')
    if secret != 'workspace2026migrate':
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        call_command('migrate', '--run-syncdb')
        return JsonResponse({'status': 'migrations complete'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def debug_db(request):
    with connection.cursor() as cursor:
        try:
            if connection.vendor == 'postgresql':
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='spaces_subscription' AND column_name='paystack_reference';")
            else:
                cursor.execute("PRAGMA table_info(spaces_subscription);")
            columns = [row[0] if connection.vendor == 'postgresql' else row[1] for row in cursor.fetchall()]
            return JsonResponse({
                'database_vendor': connection.vendor,
                'paystack_reference_exists': 'paystack_reference' in columns,
                'all_columns': columns,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)})


def health_check(request):
    return JsonResponse({"status": "healthy", "message": "API is working"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/auth/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/', include('users.urls')),
    path('api/', include('spaces.urls')),
    # path('api/team/', include('teams.urls')),
    
    # Utilities
    path('debug-db/', debug_db, name='debug_db'),
    path('health/', health_check, name='health_check'),
    path('run-migrations/', run_migrations, name='run_migrations'),
    path('create-admin/', create_admin, name='create_admin'),
]
