"""
Management command to rotate to the next variant in an A/B test.
Useful for testing and manual variant rotation.

Usage:
    python manage.py rotate_variant <test_id>
    
Example:
    python manage.py rotate_variant 1
"""

from django.core.management.base import BaseCommand, CommandError
from abtesting.models import ABTest
from abtesting.scheduler import VariantScheduler


class Command(BaseCommand):
    help = 'Rotate to the next variant in an A/B test'

    def add_arguments(self, parser):
        parser.add_argument('test_id', type=int, help='ID of the A/B test')

    def handle(self, *args, **options):
        test_id = options['test_id']

        try:
            # Get the test
            test = ABTest.objects.get(id=test_id)
            self.stdout.write(f"Found test: {test.video_title} (Status: {test.status})")
            
            # Get current variant
            scheduler = VariantScheduler(user=test.creator)
            current_variant, error = scheduler.get_current_variant(test_id)
            
            if current_variant:
                self.stdout.write(f"Current variant: {current_variant.variant_name}")
            else:
                self.stdout.write("No variant currently applied")
            
            # Rotate to next variant
            self.stdout.write(self.style.WARNING(f"\nRotating to next variant..."))
            
            next_variant, error = scheduler.rotate_variant(test_id)
            
            if next_variant:
                # Refresh from database to get updated applied_at
                next_variant.refresh_from_db()
                
                self.stdout.write(self.style.SUCCESS(f"✓ Successfully rotated to variant {next_variant.variant_name}!"))
                self.stdout.write(f"  Video ID: {test.video_id}")
                self.stdout.write(f"  Applied at: {next_variant.applied_at}")
                
                if test.test_type == 'thumbnail':
                    self.stdout.write(f"  Thumbnail: {next_variant.thumbnail_url}")
                elif test.test_type == 'title':
                    self.stdout.write(f"  Title: {next_variant.title}")
                elif test.test_type == 'combined':
                    self.stdout.write(f"  Thumbnail: {next_variant.thumbnail_url}")
                    self.stdout.write(f"  Title: {next_variant.title}")
            else:
                raise CommandError(f"Failed to rotate variant: {error}")
                
        except ABTest.DoesNotExist:
            raise CommandError(f"Test with ID {test_id} not found")
        except Exception as e:
            raise CommandError(f"Error: {str(e)}")
