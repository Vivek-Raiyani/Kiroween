"""
Variant Scheduler for rotating and applying A/B test variants.
"""

from django.utils import timezone
from django.db import transaction
from .models import ABTest, TestVariant, TestLog
from integrations.youtube import YouTubeService
from googleapiclient.http import MediaFileUpload
import logging
import requests
import tempfile
import os


logger = logging.getLogger(__name__)


class VariantScheduler:
    """Service for scheduling and rotating A/B test variants."""
    
    def __init__(self, user=None):
        """Initialize the scheduler with optional user context."""
        self.user = user
    
    def get_current_variant(self, test_id):
        """
        Get the currently active variant for a test.
        
        Args:
            test_id: ID of the test
            
        Returns:
            Tuple of (TestVariant instance or None, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Get the most recently applied variant
            current_variant = test.variants.filter(
                applied_at__isnull=False
            ).order_by('-applied_at').first()
            
            # If no variant has been applied yet, return the first variant
            if not current_variant:
                current_variant = test.variants.order_by('variant_name').first()
            
            return current_variant, None
            
        except ABTest.DoesNotExist:
            return None, "Test not found"
        except Exception as e:
            return None, f"Failed to get current variant: {str(e)}"
    
    def rotate_variant(self, test_id):
        """
        Rotate to the next variant in the test sequence.
        
        Args:
            test_id: ID of the test
            
        Returns:
            Tuple of (next TestVariant instance, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Validate test is active
            if test.status != 'active':
                return None, f"Cannot rotate variants for test with status '{test.status}'"
            
            # Get current variant
            current_variant, error = self.get_current_variant(test_id)
            if error:
                return None, error
            
            # Get all variants ordered by name
            all_variants = list(test.variants.order_by('variant_name'))
            
            if not all_variants:
                return None, "Test has no variants"
            
            # Find next variant
            if not current_variant:
                next_variant = all_variants[0]
            else:
                try:
                    current_index = all_variants.index(current_variant)
                    next_index = (current_index + 1) % len(all_variants)
                    next_variant = all_variants[next_index]
                except ValueError:
                    # Current variant not in list, start from beginning
                    next_variant = all_variants[0]
            
            # Apply the next variant
            success, error = self.apply_variant(test_id, next_variant.id)
            if not success:
                return None, error
            
            return next_variant, None
            
        except ABTest.DoesNotExist:
            return None, "Test not found"
        except Exception as e:
            return None, f"Failed to rotate variant: {str(e)}"
    
    def apply_variant(self, test_id, variant_id):
        """
        Apply a specific variant to the YouTube video.
        
        Args:
            test_id: ID of the test
            variant_id: ID of the variant to apply
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            variant = TestVariant.objects.get(id=variant_id, test=test)
            
            # Validate test is active
            if test.status != 'active':
                return False, f"Cannot apply variant for test with status '{test.status}'"
            
            # Get YouTube service
            youtube_service = YouTubeService(user=test.creator)
            service, error = youtube_service.get_service()
            if not service:
                return False, error or "Could not connect to YouTube"
            
            # Apply variant based on test type
            try:
                if test.test_type == 'thumbnail':
                    success, error = self._apply_thumbnail(service, test.video_id, variant.thumbnail_url)
                    if not success:
                        return False, error
                
                elif test.test_type == 'title':
                    success, error = self._apply_title(service, test.video_id, variant.title)
                    if not success:
                        return False, error
                
                elif test.test_type == 'description':
                    success, error = self._apply_description(service, test.video_id, variant.description)
                    if not success:
                        return False, error
                
                elif test.test_type == 'combined':
                    # Apply both thumbnail and title atomically
                    success, error = self._apply_combined(
                        service, test.video_id, 
                        variant.thumbnail_url, variant.title
                    )
                    if not success:
                        return False, error
                
                else:
                    return False, f"Unknown test type: {test.test_type}"
                
                # Update variant applied timestamp
                with transaction.atomic():
                    variant.applied_at = timezone.now()
                    variant.save()
                    
                    # Log variant change
                    TestLog.objects.create(
                        test=test,
                        action='variant_changed',
                        user=self.user,
                        details={
                            'variant_id': variant.id,
                            'variant_name': variant.variant_name,
                            'applied_at': variant.applied_at.isoformat(),
                            'test_type': test.test_type
                        }
                    )
                
                logger.info(f"Applied variant {variant.variant_name} to video {test.video_id}")
                return True, None
                
            except Exception as e:
                logger.error(f"Failed to apply variant to YouTube: {e}")
                return False, f"Failed to apply variant to YouTube: {str(e)}"
            
        except ABTest.DoesNotExist:
            return False, "Test not found"
        except TestVariant.DoesNotExist:
            return False, "Variant not found"
        except Exception as e:
            return False, f"Failed to apply variant: {str(e)}"
    
    def schedule_rotation(self, test_id):
        """
        Schedule the next variant rotation for a test.
        
        Note: This method prepares rotation scheduling information.
        Actual scheduling should be handled by Celery tasks or cron jobs.
        
        Args:
            test_id: ID of the test
            
        Returns:
            Tuple of (next_rotation_time, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Validate test is active
            if test.status != 'active':
                return None, f"Cannot schedule rotation for test with status '{test.status}'"
            
            # Get current variant to determine last rotation time
            current_variant, error = self.get_current_variant(test_id)
            if error:
                return None, error
            
            # Calculate next rotation time
            if current_variant and current_variant.applied_at:
                from datetime import timedelta
                next_rotation = current_variant.applied_at + timedelta(hours=test.rotation_frequency_hours)
            else:
                # No variant applied yet, schedule immediately
                next_rotation = timezone.now()
            
            return next_rotation, None
            
        except ABTest.DoesNotExist:
            return None, "Test not found"
        except Exception as e:
            return None, f"Failed to schedule rotation: {str(e)}"
    
    def _apply_thumbnail(self, service, video_id, thumbnail_url):
        """
        Apply a thumbnail to a YouTube video.
        
        Args:
            service: Authenticated YouTube service
            video_id: YouTube video ID
            thumbnail_url: URL of the thumbnail to apply
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            # Download thumbnail from URL
            response = requests.get(thumbnail_url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            try:
                # Upload thumbnail to YouTube
                service.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(temp_path, mimetype='image/jpeg')
                ).execute()
                
                return True, None
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except requests.exceptions.RequestException as e:
            return False, f"Failed to download thumbnail: {str(e)}"
        except Exception as e:
            return False, f"Failed to set thumbnail: {str(e)}"
    
    def _apply_title(self, service, video_id, title):
        """
        Apply a title to a YouTube video.
        
        Args:
            service: Authenticated YouTube service
            video_id: YouTube video ID
            title: New title for the video
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            # Get current video details
            video_response = service.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                return False, f"Video {video_id} not found"
            
            video = video_response['items'][0]
            
            # Update title
            video['snippet']['title'] = title
            
            # Update video
            service.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': video['snippet']
                }
            ).execute()
            
            return True, None
            
        except Exception as e:
            return False, f"Failed to update title: {str(e)}"
    
    def _apply_description(self, service, video_id, description):
        """
        Apply a description to a YouTube video.
        
        Args:
            service: Authenticated YouTube service
            video_id: YouTube video ID
            description: New description for the video
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            # Get current video details
            video_response = service.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                return False, f"Video {video_id} not found"
            
            video = video_response['items'][0]
            
            # Update description
            video['snippet']['description'] = description
            
            # Update video
            service.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': video['snippet']
                }
            ).execute()
            
            return True, None
            
        except Exception as e:
            return False, f"Failed to update description: {str(e)}"
    
    def _apply_combined(self, service, video_id, thumbnail_url, title):
        """
        Apply both thumbnail and title to a YouTube video atomically.
        
        Args:
            service: Authenticated YouTube service
            video_id: YouTube video ID
            thumbnail_url: URL of the thumbnail to apply
            title: New title for the video
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            # First update the title
            success, error = self._apply_title(service, video_id, title)
            if not success:
                return False, f"Failed to update title in combined test: {error}"
            
            # Then update the thumbnail
            success, error = self._apply_thumbnail(service, video_id, thumbnail_url)
            if not success:
                # Title was updated but thumbnail failed
                # Log this but don't rollback title (YouTube API doesn't support transactions)
                logger.warning(f"Thumbnail update failed in combined test for video {video_id}: {error}")
                return False, f"Failed to update thumbnail in combined test: {error}"
            
            return True, None
            
        except Exception as e:
            return False, f"Failed to apply combined variant: {str(e)}"
