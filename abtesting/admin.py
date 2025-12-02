from django.contrib import admin
from .models import ABTest, TestVariant, TestResult, TestLog


@admin.register(ABTest)
class ABTestAdmin(admin.ModelAdmin):
    list_display = ['video_title', 'test_type', 'status', 'creator', 'start_date', 'end_date']
    list_filter = ['status', 'test_type', 'created_at']
    search_fields = ['video_title', 'video_id', 'creator__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'


@admin.register(TestVariant)
class TestVariantAdmin(admin.ModelAdmin):
    list_display = ['variant_name', 'test', 'impressions', 'clicks', 'views', 'ctr', 'is_winner']
    list_filter = ['is_winner', 'created_at']
    search_fields = ['test__video_title', 'variant_name']
    readonly_fields = ['created_at', 'applied_at']


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['test', 'variant', 'metric_type', 'value', 'recorded_at']
    list_filter = ['metric_type', 'recorded_at']
    search_fields = ['test__video_title', 'variant__variant_name']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'


@admin.register(TestLog)
class TestLogAdmin(admin.ModelAdmin):
    list_display = ['test', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['test__video_title', 'user__username', 'action']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
