from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'is_staff', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('email',)
    
    # Use the default fieldsets from UserAdmin, but you can customize them
    fieldsets = UserAdmin.fieldsets
    add_fieldsets = UserAdmin.add_fieldsets

admin.site.register(CustomUser, CustomUserAdmin)

