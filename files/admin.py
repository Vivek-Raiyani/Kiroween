from django.contrib import admin
from .models import DriveFile


@admin.register(DriveFile)
class DriveFileAdmin(admin.ModelAdmin):
    """Admin interface for DriveFile model."""
    
    list_display = ['name', 'mime_type', 'get_size_display', 'creator', 'modified_time', 'cached_at']
    list_filter = ['mime_type', 'creator', 'modified_time']
    search_fields = ['name', 'file_id', 'mime_type']
    readonly_fields = ['file_id', 'cached_at']
    ordering = ['-modified_time']
    
    fieldsets = (
        ('File Information', {
            'fields': ('file_id', 'name', 'mime_type', 'size', 'web_view_link')
        }),
        ('Metadata', {
            'fields': ('creator', 'modified_time', 'cached_at')
        }),
    )
