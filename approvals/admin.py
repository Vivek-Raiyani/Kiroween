from django.contrib import admin
from .models import ApprovalRequest


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    """Admin interface for ApprovalRequest model."""
    
    list_display = ['id', 'editor', 'file', 'status', 'created_at', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'created_at', 'reviewed_at']
    search_fields = ['editor__username', 'file__name', 'description']
    readonly_fields = ['created_at', 'reviewed_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('editor', 'creator', 'file', 'description', 'status')
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'rejection_reason')
        }),
        ('YouTube Information', {
            'fields': ('youtube_video_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
