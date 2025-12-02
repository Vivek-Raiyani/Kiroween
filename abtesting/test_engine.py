"""
A/B Test Engine for managing test lifecycle and operations.
"""

from django.utils import timezone
from django.db import transaction
from .models import ABTest, TestVariant, TestLog
from datetime import timedelta


class ABTestEngine:
    """Service for managing A/B test lifecycle operations."""
    
    def __init__(self, user=None):
        """Initialize the test engine with optional user context."""
        self.user = user
    
    def create_test(self, video_id, video_title, test_type, variants_data, 
                   duration_hours, rotation_frequency_hours, 
                   performance_threshold=0.05, auto_select_winner=True):
        """
        Create a new A/B test with variants.
        
        Args:
            video_id: YouTube video ID
            video_title: Title of the video
            test_type: Type of test ('thumbnail', 'title', 'description', 'combined')
            variants_data: List of dicts with variant content
                          e.g., [{'name': 'A', 'thumbnail_url': '...', 'title': '...'}, ...]
            duration_hours: Total test duration in hours
            rotation_frequency_hours: How often to rotate variants
            performance_threshold: Minimum improvement for winner selection (default 0.05 = 5%)
            auto_select_winner: Whether to automatically select winner (default True)
            
        Returns:
            Tuple of (ABTest instance, error_message)
        """
        if not self.user:
            return None, "User is required to create a test"
        
        # Validate variant count (must be 2-3)
        if not variants_data or len(variants_data) < 2 or len(variants_data) > 3:
            return None, "Test must have between 2 and 3 variants"
        
        # Validate test type
        valid_types = ['thumbnail', 'title', 'description', 'combined']
        if test_type not in valid_types:
            return None, f"Invalid test type. Must be one of: {', '.join(valid_types)}"
        
        # Validate variant data based on test type
        for variant in variants_data:
            if not variant.get('name'):
                return None, "Each variant must have a name"
            
            if test_type == 'thumbnail' and not variant.get('thumbnail_url'):
                return None, "Thumbnail test requires thumbnail_url for each variant"
            elif test_type == 'title' and not variant.get('title'):
                return None, "Title test requires title for each variant"
            elif test_type == 'description' and not variant.get('description'):
                return None, "Description test requires description for each variant"
            elif test_type == 'combined':
                if not variant.get('thumbnail_url') or not variant.get('title'):
                    return None, "Combined test requires both thumbnail_url and title for each variant"
        
        try:
            with transaction.atomic():
                # Create the test
                test = ABTest.objects.create(
                    creator=self.user,
                    video_id=video_id,
                    video_title=video_title,
                    test_type=test_type,
                    status='draft',
                    duration_hours=duration_hours,
                    rotation_frequency_hours=rotation_frequency_hours,
                    performance_threshold=performance_threshold,
                    auto_select_winner=auto_select_winner
                )
                
                # Create variants
                for variant_data in variants_data:
                    TestVariant.objects.create(
                        test=test,
                        variant_name=variant_data['name'],
                        thumbnail_url=variant_data.get('thumbnail_url'),
                        title=variant_data.get('title'),
                        description=variant_data.get('description')
                    )
                
                # Log test creation
                TestLog.objects.create(
                    test=test,
                    action='created',
                    user=self.user,
                    details={
                        'test_type': test_type,
                        'variant_count': len(variants_data),
                        'duration_hours': duration_hours
                    }
                )
                
                return test, None
                
        except Exception as e:
            return None, f"Failed to create test: {str(e)}"
    
    def start_test(self, test_id):
        """
        Start an A/B test and apply the first variant.
        
        Args:
            test_id: ID of the test to start
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Validate test can be started
            if test.status not in ['draft', 'paused']:
                return False, f"Cannot start test with status '{test.status}'"
            
            # Validate test has variants
            if test.variants.count() < 2:
                return False, "Test must have at least 2 variants to start"
            
            with transaction.atomic():
                # Update test status
                test.status = 'active'
                if not test.start_date:
                    test.start_date = timezone.now()
                test.end_date = test.start_date + timedelta(hours=test.duration_hours)
                test.save()
                
                # Log test start
                TestLog.objects.create(
                    test=test,
                    action='started',
                    user=self.user,
                    details={
                        'start_date': test.start_date.isoformat(),
                        'end_date': test.end_date.isoformat()
                    }
                )
            
            # Apply the first variant to the YouTube video
            from .scheduler import VariantScheduler
            scheduler = VariantScheduler(user=self.user)
            
            # Get the first variant (alphabetically by name)
            first_variant = test.variants.order_by('variant_name').first()
            if first_variant:
                success, error = scheduler.apply_variant(test_id, first_variant.id)
                if not success:
                    # Test was started but variant application failed
                    # Log the error but don't fail the start operation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to apply first variant when starting test {test_id}: {error}")
                    return True, f"Test started but failed to apply first variant: {error}"
            
            return True, None
                
        except ABTest.DoesNotExist:
            return False, "Test not found"
        except Exception as e:
            return False, f"Failed to start test: {str(e)}"
    
    def pause_test(self, test_id):
        """
        Pause an active A/B test.
        
        Args:
            test_id: ID of the test to pause
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Validate test can be paused
            if test.status != 'active':
                return False, f"Cannot pause test with status '{test.status}'"
            
            with transaction.atomic():
                # Update test status
                test.status = 'paused'
                test.save()
                
                # Log test pause
                TestLog.objects.create(
                    test=test,
                    action='paused',
                    user=self.user,
                    details={
                        'paused_at': timezone.now().isoformat()
                    }
                )
                
                return True, None
                
        except ABTest.DoesNotExist:
            return False, "Test not found"
        except Exception as e:
            return False, f"Failed to pause test: {str(e)}"
    
    def resume_test(self, test_id):
        """
        Resume a paused A/B test.
        
        Args:
            test_id: ID of the test to resume
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Validate test can be resumed
            if test.status != 'paused':
                return False, f"Cannot resume test with status '{test.status}'"
            
            with transaction.atomic():
                # Update test status
                test.status = 'active'
                test.save()
                
                # Log test resume
                TestLog.objects.create(
                    test=test,
                    action='resumed',
                    user=self.user,
                    details={
                        'resumed_at': timezone.now().isoformat()
                    }
                )
                
                return True, None
                
        except ABTest.DoesNotExist:
            return False, "Test not found"
        except Exception as e:
            return False, f"Failed to resume test: {str(e)}"
    
    def stop_test(self, test_id):
        """
        Stop an A/B test early.
        
        Args:
            test_id: ID of the test to stop
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Validate test can be stopped
            if test.status not in ['active', 'paused']:
                return False, f"Cannot stop test with status '{test.status}'"
            
            with transaction.atomic():
                # Update test status
                test.status = 'completed'
                test.completed_at = timezone.now()
                test.save()
                
                # Log test stop
                TestLog.objects.create(
                    test=test,
                    action='stopped',
                    user=self.user,
                    details={
                        'stopped_at': test.completed_at.isoformat(),
                        'stopped_early': True
                    }
                )
                
                return True, None
                
        except ABTest.DoesNotExist:
            return False, "Test not found"
        except Exception as e:
            return False, f"Failed to stop test: {str(e)}"
    
    def get_test_status(self, test_id):
        """
        Get the current status and details of an A/B test.
        
        Args:
            test_id: ID of the test
            
        Returns:
            Tuple of (status dict, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Calculate progress
            progress_percentage = 0
            time_remaining = None
            
            if test.status == 'active' and test.start_date and test.end_date:
                now = timezone.now()
                total_duration = (test.end_date - test.start_date).total_seconds()
                elapsed = (now - test.start_date).total_seconds()
                
                if total_duration > 0:
                    progress_percentage = min(100, (elapsed / total_duration) * 100)
                
                if now < test.end_date:
                    time_remaining = test.end_date - now
            
            # Get variant data
            variants = []
            for variant in test.variants.all():
                variants.append({
                    'id': variant.id,
                    'name': variant.variant_name,
                    'impressions': variant.impressions,
                    'clicks': variant.clicks,
                    'views': variant.views,
                    'ctr': variant.ctr,
                    'is_winner': variant.is_winner
                })
            
            status_data = {
                'id': test.id,
                'video_id': test.video_id,
                'video_title': test.video_title,
                'test_type': test.test_type,
                'status': test.status,
                'start_date': test.start_date.isoformat() if test.start_date else None,
                'end_date': test.end_date.isoformat() if test.end_date else None,
                'completed_at': test.completed_at.isoformat() if test.completed_at else None,
                'progress_percentage': round(progress_percentage, 2),
                'time_remaining_seconds': int(time_remaining.total_seconds()) if time_remaining else None,
                'duration_hours': test.duration_hours,
                'rotation_frequency_hours': test.rotation_frequency_hours,
                'performance_threshold': test.performance_threshold,
                'auto_select_winner': test.auto_select_winner,
                'winner_variant_id': test.winner_variant_id,
                'variants': variants
            }
            
            return status_data, None
            
        except ABTest.DoesNotExist:
            return None, "Test not found"
        except Exception as e:
            return None, f"Failed to get test status: {str(e)}"
