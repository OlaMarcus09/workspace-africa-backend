from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from spaces.models import CheckIn, Subscription # Import models, NOT serializers
from django.utils import timezone

User = get_user_model()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
    def validate(self, attrs):
        attrs[self.username_field] = attrs.get('email')
        return super().validate(attrs)

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
