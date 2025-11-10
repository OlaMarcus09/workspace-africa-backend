from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from spaces.models import CheckIn, Subscription
from django.utils import timezone

User = get_user_model()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer that uses 'email' instead of 'username' for authentication
    """
    username_field = 'email'  # This tells SimpleJWT to use email as the username field

    def validate(self, attrs):
        # Ensure email is provided
        email = attrs.get('email')
        if not email:
            raise serializers.ValidationError({"email": "Email field is required."})
        
        # Try to get the user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No user found with this email address."})
        
        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError({"email": "This account is inactive."})
        
        # Add username to attrs for the parent class validation
        attrs['username'] = user.username
        
        # Now validate with parent class
        data = super().validate(attrs)
        
        # Add custom response data if needed
        data['user_id'] = user.id
        data['email'] = user.email
        data['username'] = user.username
        data['user_type'] = user.user_type
        
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['user_type'] = user.user_type
        return token

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm password')
    
    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2')
        extra_kwargs = {'username': {'required': True}}
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
            
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        validated_data.pop('password2', None)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    subscription = serializers.SerializerMethodField()
    days_used = serializers.SerializerMethodField()
    total_days = serializers.SerializerMethodField()
    team = serializers.PrimaryKeyRelatedField(read_only=True)
    managed_space = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'photo_url', 'user_type',
            'team', 'managed_space', 'subscription', 'days_used', 'total_days'
        )
    
    def get_subscription(self, obj):
        from spaces.serializers import SubscriptionSerializer 
        sub = obj.subscriptions.filter(is_active=True).first()
        if sub:
            return SubscriptionSerializer(sub).data
        return None

    def get_days_used(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        if not sub or not sub.start_date:
             return 0
        days_used = CheckIn.objects.filter(
            user=obj, 
            timestamp__gte=sub.start_date
        ).values('timestamp__date').distinct().count() 
        return days_used

    def get_total_days(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        if not sub:
            return 0
        return sub.plan.included_days

class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'photo_url')
