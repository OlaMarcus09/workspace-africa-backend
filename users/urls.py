from django.urls import path
from .views import UserRegisterView, UserProfileView, ChangePasswordView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='auth_register'),
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'), # <-- NEW URL
]