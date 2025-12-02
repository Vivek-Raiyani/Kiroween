from django.db import models
from accounts.models import User


class AnalyticsCache(models.Model):
    """Cache for YouTube Analytics API data to reduce API calls."""
    
    video_id = models.CharField(max_length=20, help_text='YouTube video ID')
    metric_type = models.CharField(
        max_length=50,
        help_text='Type of metric (views, watch_time, ctr, etc.)'
    )
    value = models.FloatField(help_text='Metric value')
    date = models.DateField(help_text='Date for this metric')
    cached_at = models.DateTimeField(auto_now=True, help_text='When this data was cached')
    
    class Meta:
        unique_together = ['video_id', 'metric_type', 'date']
        indexes = [
            models.Index(fields=['video_id', 'date']),
            models.Index(fields=['metric_type', 'date']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.video_id} - {self.metric_type} - {self.date}"


class ChannelMetrics(models.Model):
    """Store channel-level metrics over time."""
    
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text='Creator who owns this channel'
    )
    channel_id = models.CharField(max_length=50, help_text='YouTube channel ID')
    subscribers = models.IntegerField(help_text='Subscriber count')
    total_views = models.BigIntegerField(help_text='Total channel views')
    total_watch_time = models.BigIntegerField(help_text='Total watch time in minutes')
    average_view_duration = models.FloatField(help_text='Average view duration in seconds')
    date = models.DateField(help_text='Date for these metrics')
    cached_at = models.DateTimeField(auto_now=True, help_text='When this data was cached')
    
    class Meta:
        unique_together = ['channel_id', 'date']
        ordering = ['-date']
        verbose_name_plural = 'Channel metrics'
    
    def __str__(self):
        return f"{self.channel_id} - {self.date}"


class CompetitorChannel(models.Model):
    """Store competitor channels for comparison analysis."""
    
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text='Creator tracking this competitor'
    )
    competitor_channel_id = models.CharField(
        max_length=50,
        help_text='YouTube channel ID of competitor'
    )
    channel_name = models.CharField(max_length=255, help_text='Competitor channel name')
    added_at = models.DateTimeField(auto_now_add=True, help_text='When competitor was added')
    is_active = models.BooleanField(
        default=True,
        help_text='Whether to actively track this competitor'
    )
    
    class Meta:
        unique_together = ['creator', 'competitor_channel_id']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.channel_name} (tracked by {self.creator.username})"


class SEOAnalysis(models.Model):
    """Store SEO analysis results for videos."""
    
    video_id = models.CharField(max_length=20, help_text='YouTube video ID')
    title = models.CharField(max_length=255, help_text='Video title analyzed')
    description = models.TextField(help_text='Video description analyzed')
    tags = models.JSONField(help_text='Video tags analyzed')
    seo_score = models.IntegerField(help_text='SEO score (0-100)')
    keyword_suggestions = models.JSONField(help_text='Suggested keywords for optimization')
    recommendations = models.JSONField(help_text='SEO improvement recommendations')
    analyzed_at = models.DateTimeField(auto_now=True, help_text='When analysis was performed')
    
    class Meta:
        ordering = ['-analyzed_at']
        verbose_name_plural = 'SEO analyses'
    
    def __str__(self):
        return f"{self.video_id} - Score: {self.seo_score}"


class PostingRecommendation(models.Model):
    """Store optimal posting time recommendations for channels."""
    
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text='Creator for this recommendation'
    )
    channel_id = models.CharField(max_length=50, help_text='YouTube channel ID')
    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        help_text='Day of week (0=Monday, 6=Sunday)'
    )
    hour = models.IntegerField(help_text='Hour of day (0-23)')
    expected_engagement = models.FloatField(help_text='Expected engagement level')
    confidence_score = models.FloatField(help_text='Confidence in this recommendation')
    calculated_at = models.DateTimeField(auto_now=True, help_text='When recommendation was calculated')
    
    class Meta:
        ordering = ['-expected_engagement']
    
    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK)[self.day_of_week]
        return f"{self.channel_id} - {day_name} at {self.hour}:00"
