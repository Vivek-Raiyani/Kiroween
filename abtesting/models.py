from django.db import models
from django.conf import settings


class ABTest(models.Model):
    """Model for A/B testing configuration and management."""
    
    TEST_TYPE_CHOICES = [
        ('thumbnail', 'Thumbnail'),
        ('title', 'Title'),
        ('description', 'Description'),
        ('combined', 'Combined'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text='Creator who owns this test'
    )
    video_id = models.CharField(
        max_length=20,
        help_text='YouTube video ID'
    )
    video_title = models.CharField(
        max_length=255,
        help_text='Title of the video being tested'
    )
    test_type = models.CharField(
        max_length=20,
        choices=TEST_TYPE_CHOICES,
        help_text='Type of A/B test'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Current status of the test'
    )
    
    # Test timing
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the test started'
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the test should end'
    )
    duration_hours = models.IntegerField(
        help_text='Total duration of the test in hours'
    )
    rotation_frequency_hours = models.IntegerField(
        help_text='How often to rotate variants in hours'
    )
    
    # Test configuration
    performance_threshold = models.FloatField(
        default=0.05,
        help_text='Minimum improvement threshold for winner selection (e.g., 0.05 = 5%)'
    )
    auto_select_winner = models.BooleanField(
        default=True,
        help_text='Automatically select winner when test completes'
    )
    
    # Test results
    winner_variant = models.ForeignKey(
        'TestVariant',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='won_tests',
        help_text='The winning variant'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the test was completed'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'A/B Test'
        verbose_name_plural = 'A/B Tests'
    
    def __str__(self):
        return f"{self.get_test_type_display()} test for {self.video_title} ({self.get_status_display()})"



class TestVariant(models.Model):
    """Model for individual test variants with content and performance metrics."""
    
    test = models.ForeignKey(
        ABTest,
        on_delete=models.CASCADE,
        related_name='variants',
        help_text='The A/B test this variant belongs to'
    )
    variant_name = models.CharField(
        max_length=10,
        help_text='Variant identifier (e.g., A, B, C)'
    )
    
    # Variant content
    thumbnail_url = models.URLField(
        null=True,
        blank=True,
        help_text='URL of the thumbnail for this variant'
    )
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Title text for this variant'
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text='Description text for this variant'
    )
    
    # Performance metrics
    impressions = models.IntegerField(
        default=0,
        help_text='Number of times the variant was shown'
    )
    clicks = models.IntegerField(
        default=0,
        help_text='Number of clicks on the variant'
    )
    views = models.IntegerField(
        default=0,
        help_text='Number of video views from this variant'
    )
    ctr = models.FloatField(
        default=0.0,
        help_text='Click-through rate (clicks/impressions)'
    )
    
    # Status
    is_winner = models.BooleanField(
        default=False,
        help_text='Whether this variant won the test'
    )
    applied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this variant was applied to YouTube'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['test', 'variant_name']
        unique_together = ['test', 'variant_name']
        verbose_name = 'Test Variant'
        verbose_name_plural = 'Test Variants'
    
    def __str__(self):
        return f"Variant {self.variant_name} for {self.test.video_title}"



class TestResult(models.Model):
    """Model for storing test metrics over time."""
    
    test = models.ForeignKey(
        ABTest,
        on_delete=models.CASCADE,
        related_name='results',
        help_text='The A/B test these results belong to'
    )
    variant = models.ForeignKey(
        TestVariant,
        on_delete=models.CASCADE,
        related_name='results',
        help_text='The variant these results are for'
    )
    metric_type = models.CharField(
        max_length=50,
        help_text='Type of metric (e.g., impressions, clicks, views, ctr)'
    )
    value = models.FloatField(
        help_text='The metric value'
    )
    recorded_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this metric was recorded'
    )
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['test', 'variant', 'metric_type']),
            models.Index(fields=['recorded_at']),
        ]
        verbose_name = 'Test Result'
        verbose_name_plural = 'Test Results'
    
    def __str__(self):
        return f"{self.metric_type}={self.value} for {self.variant.variant_name} at {self.recorded_at}"



class TestLog(models.Model):
    """Model for audit logging of test actions."""
    
    test = models.ForeignKey(
        ABTest,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text='The A/B test this log entry is for'
    )
    action = models.CharField(
        max_length=50,
        help_text='Action performed (e.g., created, started, paused, completed, variant_changed)'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text='User who performed the action'
    )
    details = models.JSONField(
        default=dict,
        help_text='Additional details about the action'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When the action occurred'
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['test', 'timestamp']),
            models.Index(fields=['action']),
        ]
        verbose_name = 'Test Log'
        verbose_name_plural = 'Test Logs'
    
    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"{self.action} by {user_str} at {self.timestamp}"
