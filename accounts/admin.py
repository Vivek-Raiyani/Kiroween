from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Team


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role and team fields."""
    
    list_display = ['username', 'email', 'role', 'creator', 'invitation_accepted', 'is_staff']
    list_filter = ['role', 'invitation_accepted', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Team', {
            'fields': ('role', 'creator', 'invited_by', 'invitation_token', 'invitation_accepted')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Team', {
            'fields': ('role', 'creator', 'invited_by')
        }),
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Team admin interface."""
    
    list_display = ['creator', 'created_at', 'member_count']
    search_fields = ['creator__username']
    filter_horizontal = ['members']
    
    def member_count(self, obj):
        return obj.members.count()
    
    member_count.short_description = 'Members'
