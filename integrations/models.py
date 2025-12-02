from django.db import models
from django.conf import settings


class Integration(models.Model):
    """Model for storing OAuth integration credentials."""
    
    SERVICE_CHOICES = [
        ('google_drive', 'Google Drive'),
        ('youtube', 'YouTube'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='integrations',
        help_text='The user who owns this integration'
    )
    
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_CHOICES,
        help_text='Type of service integration'
    )
    
    access_token = models.TextField(
        help_text='OAuth access token (encrypted)'
    )
    
    refresh_token = models.TextField(
        help_text='OAuth refresh token (encrypted)'
    )
    
    expires_at = models.DateTimeField(
        help_text='Token expiration timestamp'
    )
    
    scopes = models.TextField(
        blank=True,
        default='',
        help_text='Granted OAuth scopes (space-separated)'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the integration was created'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the integration was last updated'
    )
    
    class Meta:
        unique_together = ['user', 'service_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_service_type_display()}"
    
    def is_expired(self):
        """Check if the access token is expired."""
        from django.utils import timezone
        return timezone.now() >= self.expires_at
