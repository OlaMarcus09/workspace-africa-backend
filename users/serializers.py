class UserProfileSerializerDetailed(serializers.ModelSerializer):
    subscription = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    days_used = serializers.SerializerMethodField()
    total_days = serializers.SerializerMethodField()
    total_checkins = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'phone', 'photo_url', 'user_type',
            'team', 'managed_space', 'subscription', 'plan_name', 
            'days_used', 'total_days', 'total_checkins'
        )
        read_only_fields = (
            'id', 'user_type', 'team', 'managed_space', 'subscription', 
            'plan_name', 'days_used', 'total_days', 'total_checkins'
        )
    
    def _get_active_sub(self, obj):
        # Defend against missing related names on the User model
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
            # Defend against missing checkin query paths
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
        
        # Safely read field duration regardless of whether it's named 'included_days', 'days', or missing
        plan = sub.plan
        days = getattr(plan, 'included_days', getattr(plan, 'days', 30))
        
        # Return 999 to signal "Unlimited" to frontend
        return 999 if days >= 30 else days
