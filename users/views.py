from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from .serializers import UserRegisterSerializer, UserProfileSerializer # Import new serializer

User = get_user_model()

class UserRegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny] 

# --- NEW VIEW ---
class UserProfileView(generics.RetrieveAPIView):
    """
    API endpoint for getting the current logged-in user's profile.
    GET /api/users/me/
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated] # Must be logged in

    def get_object(self):
        # This view doesn't take an ID from the URL,
        # it just returns the user from the request.
        return self.request.user
