from django.contrib import admin
from .models import Plan, PartnerSpace, Subscription, CheckIn, CheckInToken

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_ngn', 'included_days', 'access_tier', 'paystack_plan_code')
    search_fields = ('name',)

@admin.register(PartnerSpace)
class PartnerSpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'access_tier', 'amenities')
    search_fields = ('name', 'address')
    list_filter = ('access_tier',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'start_date', 'end_date')
    search_fields = ('user__email', 'plan__name')
    list_filter = ('is_active', 'plan')

@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('user', 'space', 'timestamp')
    search_fields = ('user__email', 'space__name')
    list_filter = ('space',)
    date_hierarchy = 'timestamp'

@admin.register(CheckInToken)
class CheckInTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'expires_at')
    search_fields = ('user__email', 'code')
