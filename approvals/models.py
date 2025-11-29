from django.db import models
from django.conf import settings
from files.models import DriveFile


class ApprovalRequest(models.Model):
    """Model for video approval requests from editors to managers/creators."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('uploaded', 'Uploaded'),
    ]
    
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_requests',
        help_text='The editor who submitted this request'
    )
    
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_requests',
        help_text='The creator who owns the team'
    )
    
    file = models.ForeignKey(
        DriveFile,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        help_text='The video file to be approved'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Optional description or notes about the video'
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current status of the approval request'
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_requests',
        help_text='The manager or creator who reviewed this request'
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the request was reviewed'
    )
    
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection (if rejected)'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the request was created'
    )
    
    youtube_video_id = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text='YouTube video ID after upload'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['editor', '-created_at']),
            models.Index(fields=['creator', 'status', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Request by {self.editor.username} for {self.file.name} ({self.status})"
    
    def is_pending(self):
        """Check if request is pending."""
        return self.status == 'pending'
    
    def is_approved(self):
        """Check if request is approved."""
        return self.status == 'approved'
    
    def is_rejected(self):
        """Check if request is rejected."""
        return self.status == 'rejected'
    
    def is_uploaded(self):
        """Check if video has been uploaded."""
        return self.status == 'uploaded'
    
    def can_be_reviewed(self):
        """Check if request can be reviewed (is pending)."""
        return self.is_pending()
    
    def can_be_uploaded(self):
        """Check if request can be uploaded to YouTube (is approved)."""
        return self.is_approved()
