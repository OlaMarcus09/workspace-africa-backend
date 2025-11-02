from django.urls import path
from .views import UserRegisterView, UserProfileView # Import new view

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='auth_register'),
    path('me/', UserProfileView.as_view(), name='user_profile'), # <-- NEW URL
]
