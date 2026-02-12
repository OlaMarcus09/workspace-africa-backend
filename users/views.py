from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserRegisterSerializer, 
    UserProfileSerializerDetailed, # Imported the detailed one
    MyTokenObtainPairSerializer
)

User = get_user_model()

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny] 

class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    # SWITCHED: Now uses the Detailed serializer
    serializer_class = UserProfileSerializerDetailed
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user