from rest_framework import serializers
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
        )


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['user_type'] = user.user_type
        return token


class UserProfileSerializerDetailed(serializers.ModelSerializer):
    subscription = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    days_used = serializers.SerializerMethodField()
    total_days = serializers.SerializerMethodField()
    total_checkins = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'photo_url', 'user_type',
            'team', 'managed_space', 'subscription', 'plan_name',
            'days_used', 'total_days', 'total_checkins'
        )
        read_only_fields = (
            'id', 'user_type', 'team', 'managed_space', 'subscription',
            'plan_name', 'days_used', 'total_days', 'total_checkins'
        )

    def _get_active_sub(self, obj):
        try:
            if hasattr(obj, 'subscriptions'):
                return obj.subscriptions.filter(is_active=True).first()
            elif hasattr(obj, 'subscription_set'):
                return obj.subscription_set.filter(is_active=True).first()
        except Exception:
            return None
        return None

    def get_subscription(self, obj):
        sub = self._get_active_sub(obj)
        if sub:
            try:
                from spaces.serializers import SubscriptionSerializer
                return SubscriptionSerializer(sub).data
            except Exception:
                return None
        return None

    def get_plan_name(self, obj):
        sub = self._get_active_sub(obj)
        if sub and getattr(sub, 'plan', None):
            return getattr(sub.plan, 'name', 'FREE_TIER')
        return "FREE_TIER"

    def get_total_checkins(self, obj):
        try:
            if hasattr(obj, 'check_ins'):
                return obj.check_ins.count()
            elif hasattr(obj, 'checkin_set'):
                return obj.checkin_set.count()
        except Exception:
            return 0
        return 0

    def get_days_used(self, obj):
        sub = self._get_active_sub(obj)
        if not sub or not getattr(sub, 'start_date', None):
            return 0
        try:
            checkins_mgr = getattr(obj, 'check_ins', getattr(obj, 'checkin_set', None))
            if checkins_mgr:
                return checkins_mgr.filter(
                    timestamp__gte=sub.start_date
                ).values('timestamp__date').distinct().count()
        except Exception:
            return 0
        return 0

    def get_total_days(self, obj):
        sub = self._get_active_sub(obj)
        if not sub or not getattr(sub, 'plan', None):
            return 0
        plan = sub.plan
        days = getattr(plan, 'included_days', getattr(plan, 'days', 30))
        return 999 if days >= 30 else days
