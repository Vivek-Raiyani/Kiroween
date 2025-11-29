from django.contrib import admin
from .models import Integration


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    """Admin interface for Integration model."""
    
    list_display = ['user', 'service_type', 'created_at', 'expires_at', 'is_expired']
    list_filter = ['service_type', 'created_at', 'expires_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'service_type')
        }),
        ('OAuth Tokens', {
            'fields': ('access_token', 'refresh_token', 'expires_at'),
            'description': 'OAuth tokens are encrypted for security.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired(self, obj):
        """Display whether the integration is expired."""
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
