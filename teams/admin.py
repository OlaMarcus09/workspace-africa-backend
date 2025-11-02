from django.contrib import admin
from .models import Team, Invitation

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin')
    search_fields = ('name', 'admin__email')

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('team', 'email', 'status', 'created_at')
    search_fields = ('team__name', 'email')
    list_filter = ('status', 'team')
