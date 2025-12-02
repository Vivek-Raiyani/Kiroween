"""
Metrics Collector for gathering and updating A/B test variant performance metrics.
"""

from django.utils import timezone
from django.db import transaction
from .models import ABTest, TestVariant, TestResult
from integrations.youtube import YouTubeAnalyticsService
import logging
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class MetricsCollector:
    """Service for collecting and updating A/B test variant metrics."""
    
    def __init__(self, user=None):
        """Initialize the metrics collector with optional user context."""
        self.user = user
    
    def collect_variant_metrics(self, test_id):
        """
        Collect metrics for all variants in a test from YouTube Analytics API.
        
        This method fetches the latest performance data for each variant and
        updates the variant statistics accordingly.
        
        Args:
            test_id: ID of the test
            
        Returns:
            Tuple of (metrics dict, error_message)
            metrics dict format: {
                'test_id': int,
                'collected_at': str (ISO format),
                'variants': [
                    {
                        'variant_id': int,
                        'variant_name': str,
                        'impressions': int,
                        'clicks': int,
                        'views': int,
                        'ctr': float
                    },
                    ...
                ]
            }
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Validate test is active or completed
            if test.status not in ['active', 'completed']:
                return None, f"Cannot collect metrics for test with status '{test.status}'"
            
            # Get YouTube Analytics service
            analytics_service = YouTubeAnalyticsService(user=test.creator)
            
            # Determine date range for metrics collection
            # Use test start date to now (or completion date if completed)
            if not test.start_date:
                return None, "Test has not been started yet"
            
            start_date = test.start_date.date()
            end_date = test.completed_at.date() if test.completed_at else timezone.now().date()
            
            # Fetch video metrics from YouTube Analytics API
            video_metrics, error = analytics_service.get_video_metrics(
                test.video_id,
                start_date,
                end_date
            )
            
            if error:
                logger.error(f"Failed to fetch video metrics for test {test_id}: {error}")
                return None, error
            
            # Calculate total metrics from the response
            total_views = 0
            total_watch_time = 0
            
            if video_metrics and 'rows' in video_metrics:
                for row in video_metrics['rows']:
                    total_views += int(row.get('views', 0))
                    total_watch_time += int(row.get('estimatedMinutesWatched', 0))
            
            # Get all variants for this test
            variants = test.variants.all()
            
            if not variants:
                return None, "Test has no variants"
            
            # For A/B testing, we need to track metrics per variant
            # Since YouTube doesn't track metrics per thumbnail/title variant directly,
            # we need to estimate based on the time periods each variant was active
            
            collected_metrics = {
                'test_id': test_id,
                'collected_at': timezone.now().isoformat(),
                'variants': []
            }
            
            # Calculate metrics for each variant based on when it was active
            for variant in variants:
                # Get the time periods when this variant was active
                variant_metrics = self._calculate_variant_metrics(
                    test,
                    variant,
                    video_metrics,
                    start_date,
                    end_date
                )
                
                # Update variant statistics
                success, error = self.update_variant_stats(variant.id, variant_metrics)
                if not success:
                    logger.warning(f"Failed to update stats for variant {variant.id}: {error}")
                
                collected_metrics['variants'].append({
                    'variant_id': variant.id,
                    'variant_name': variant.variant_name,
                    'impressions': variant_metrics['impressions'],
                    'clicks': variant_metrics['clicks'],
                    'views': variant_metrics['views'],
                    'ctr': variant_metrics['ctr']
                })
            
            logger.info(f"Collected metrics for test {test_id} with {len(variants)} variants")
            return collected_metrics, None
            
        except ABTest.DoesNotExist:
            return None, "Test not found"
        except Exception as e:
            logger.error(f"Failed to collect variant metrics: {e}")
            return None, f"Failed to collect variant metrics: {str(e)}"
    
    def _calculate_variant_metrics(self, test, variant, video_metrics, start_date, end_date):
        """
        Calculate metrics for a specific variant based on when it was active.
        
        This is an estimation method since YouTube doesn't track metrics per variant.
        We calculate based on the time periods when each variant was active.
        
        Args:
            test: ABTest instance
            variant: TestVariant instance
            video_metrics: Video metrics from YouTube Analytics API
            start_date: Start date for metrics
            end_date: End date for metrics
            
        Returns:
            Dict with impressions, clicks, views, and ctr
        """
        # Get all variant changes from test logs
        variant_periods = self._get_variant_active_periods(test, variant)
        
        # If variant was never applied, return zeros
        if not variant_periods:
            return {
                'impressions': 0,
                'clicks': 0,
                'views': 0,
                'ctr': 0.0
            }
        
        # Calculate metrics for each period the variant was active
        total_views = 0
        
        if video_metrics and 'rows' in video_metrics:
            for row in video_metrics['rows']:
                row_date_str = row.get('day', '')
                if not row_date_str:
                    continue
                
                try:
                    row_date = datetime.strptime(row_date_str, '%Y-%m-%d').date()
                except ValueError:
                    continue
                
                # Check if this date falls within any period when this variant was active
                for period_start, period_end in variant_periods:
                    if period_start <= row_date <= period_end:
                        total_views += int(row.get('views', 0))
                        break
        
        # Estimate impressions and clicks based on typical CTR patterns
        # For A/B testing, we use a simplified model:
        # - Impressions are estimated as views * 10 (typical impression-to-view ratio)
        # - Clicks are estimated as views (since a view requires a click on the thumbnail)
        
        estimated_impressions = total_views * 10
        estimated_clicks = total_views
        
        # Calculate CTR
        ctr = self.calculate_variant_ctr(estimated_impressions, estimated_clicks)
        
        return {
            'impressions': estimated_impressions,
            'clicks': estimated_clicks,
            'views': total_views,
            'ctr': ctr
        }
    
    def _get_variant_active_periods(self, test, variant):
        """
        Get the time periods when a variant was active.
        
        Args:
            test: ABTest instance
            variant: TestVariant instance
            
        Returns:
            List of tuples (start_date, end_date) when variant was active
        """
        from .models import TestLog
        
        # Get all variant change logs for this test
        variant_changes = TestLog.objects.filter(
            test=test,
            action='variant_changed'
        ).order_by('timestamp')
        
        periods = []
        current_start = None
        
        for log in variant_changes:
            variant_id = log.details.get('variant_id')
            
            if variant_id == variant.id:
                # This variant became active
                current_start = log.timestamp.date()
            elif current_start:
                # Another variant became active, end the current period
                periods.append((current_start, log.timestamp.date()))
                current_start = None
        
        # If variant is still active, extend to now or test end
        if current_start:
            end_date = test.completed_at.date() if test.completed_at else timezone.now().date()
            periods.append((current_start, end_date))
        
        return periods
    
    def update_variant_stats(self, variant_id, metrics):
        """
        Update the performance statistics for a variant.
        
        Args:
            variant_id: ID of the variant to update
            metrics: Dict with impressions, clicks, views, and ctr
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            variant = TestVariant.objects.get(id=variant_id)
            
            # Validate metrics
            if not isinstance(metrics, dict):
                return False, "Metrics must be a dictionary"
            
            required_keys = ['impressions', 'clicks', 'views', 'ctr']
            for key in required_keys:
                if key not in metrics:
                    return False, f"Missing required metric: {key}"
            
            # Update variant with new metrics
            with transaction.atomic():
                variant.impressions = metrics['impressions']
                variant.clicks = metrics['clicks']
                variant.views = metrics['views']
                variant.ctr = metrics['ctr']
                variant.save()
                
                # Record metrics in TestResult for historical tracking
                TestResult.objects.create(
                    test=variant.test,
                    variant=variant,
                    metric_type='impressions',
                    value=metrics['impressions']
                )
                TestResult.objects.create(
                    test=variant.test,
                    variant=variant,
                    metric_type='clicks',
                    value=metrics['clicks']
                )
                TestResult.objects.create(
                    test=variant.test,
                    variant=variant,
                    metric_type='views',
                    value=metrics['views']
                )
                TestResult.objects.create(
                    test=variant.test,
                    variant=variant,
                    metric_type='ctr',
                    value=metrics['ctr']
                )
            
            logger.info(f"Updated stats for variant {variant_id}: {metrics}")
            return True, None
            
        except TestVariant.DoesNotExist:
            return False, "Variant not found"
        except Exception as e:
            logger.error(f"Failed to update variant stats: {e}")
            return False, f"Failed to update variant stats: {str(e)}"
    
    def calculate_variant_ctr(self, impressions, clicks=None):
        """
        Calculate click-through rate for a variant.
        
        CTR = (clicks / impressions) * 100
        
        Args:
            impressions: Number of impressions (can be int or TestVariant instance)
            clicks: Number of clicks (optional if impressions is TestVariant)
            
        Returns:
            Float representing CTR as a percentage (0-100)
        """
        # Handle case where impressions is a TestVariant instance
        if isinstance(impressions, TestVariant):
            variant = impressions
            impressions = variant.impressions
            clicks = variant.clicks
        
        # Validate inputs
        if not isinstance(impressions, (int, float)) or not isinstance(clicks, (int, float)):
            logger.warning(f"Invalid CTR calculation inputs: impressions={impressions}, clicks={clicks}")
            return 0.0
        
        if impressions <= 0:
            return 0.0
        
        # Calculate CTR as percentage
        ctr = (clicks / impressions) * 100
        
        # Round to 2 decimal places
        return round(ctr, 2)
