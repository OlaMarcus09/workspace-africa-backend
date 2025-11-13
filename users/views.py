from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.views import APIView
import traceback
from .serializers import (
    UserRegisterSerializer, 
    UserProfileSerializer,
    MyTokenObtainPairSerializer
)

User = get_user_model()

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny] 

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserProfileSerializer(user)
            return Response(serializer.data)
        except Exception as e:
            # Return the actual error for debugging
            return Response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
