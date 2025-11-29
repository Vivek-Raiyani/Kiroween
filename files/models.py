from django.db import models
from django.conf import settings


class DriveFile(models.Model):
    """Model for caching Google Drive file metadata."""
    
    file_id = models.CharField(
        max_length=255,
        unique=True,
        help_text='Google Drive file ID'
    )
    
    name = models.CharField(
        max_length=255,
        help_text='File name'
    )
    
    mime_type = models.CharField(
        max_length=100,
        help_text='MIME type of the file'
    )
    
    size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='File size in bytes'
    )
    
    modified_time = models.DateTimeField(
        help_text='Last modification time from Google Drive'
    )
    
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='drive_files',
        help_text='The creator who owns this file'
    )
    
    cached_at = models.DateTimeField(
        auto_now=True,
        help_text='When the metadata was last cached'
    )
    
    web_view_link = models.URLField(
        null=True,
        blank=True,
        help_text='Link to view the file in Google Drive'
    )
    
    class Meta:
        ordering = ['-modified_time']
        indexes = [
            models.Index(fields=['creator', '-modified_time']),
            models.Index(fields=['file_id']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.file_id})"
    
    def get_size_display(self):
        """Return human-readable file size."""
        if not self.size:
            return 'Unknown'
        
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
