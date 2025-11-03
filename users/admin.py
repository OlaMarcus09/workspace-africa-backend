from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    # --- UPDATED ---
    # Show our new fields in the main list
    list_display = (
        'email', 
        'username', 
        'user_type', # <-- ADDED
        'team',      # <-- ADDED
        'managed_space', # <-- ADDED
        'is_staff'
    )
    
    # --- UPDATED ---
    # Add our new fields to the "Edit User" page
    # We'll add a new section called "Workspace Africa Roles"
    
    # We take the default fieldsets from UserAdmin...
    fieldsets = list(UserAdmin.fieldsets)
    # ...and add our new section
    fieldsets.append(
        ('Workspace Africa Roles', {
            'fields': (
                'user_type', 
                'team', 
                'managed_space',
                'photo_url'
            ),
        })
    )
    
    # Add our new fields to the "Add User" page
    add_fieldsets = list(UserAdmin.add_fieldsets)
    add_fieldsets.append(
        ('Workspace Africa Roles', {
            'fields': (
                'user_type', 
                'team', 
                'managed_space',
                'photo_url'
            ),
        })
    )

    # Make our new fields filterable
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'username')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
