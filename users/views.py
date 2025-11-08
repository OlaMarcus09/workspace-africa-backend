from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserRegisterSerializer, 
    UserProfileSerializer,
    MyTokenObtainPairSerializer # <-- Import our new serializer
)

User = get_user_model()

# --- NEW VIEW ---
class MyTokenObtainPairView(TokenObtainPairView):
    """
    This view uses our custom serializer to log in with email.
    """
    serializer_class = MyTokenObtainPairSerializer

# --- (Rest of the file is the same) ---

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny] 

class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
