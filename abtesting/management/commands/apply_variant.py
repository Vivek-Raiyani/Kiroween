"""
Management command to manually apply a variant to a YouTube video.
Useful for testing and troubleshooting A/B tests.

Usage:
    python manage.py apply_variant <test_id> <variant_name>
    
Example:
    python manage.py apply_variant 1 A
    python manage.py apply_variant 1 B
"""

from django.core.management.base import BaseCommand, CommandError
from abtesting.models import ABTest, TestVariant
from abtesting.scheduler import VariantScheduler


class Command(BaseCommand):
    help = 'Manually apply a variant to a YouTube video for testing'

    def add_arguments(self, parser):
        parser.add_argument('test_id', type=int, help='ID of the A/B test')
        parser.add_argument('variant_name', type=str, help='Name of the variant to apply (A, B, or C)')

    def handle(self, *args, **options):
        test_id = options['test_id']
        variant_name = options['variant_name'].upper()

        try:
            # Get the test
            test = ABTest.objects.get(id=test_id)
            self.stdout.write(f"Found test: {test.video_title} (Status: {test.status})")
            
            # Get the variant
            try:
                variant = test.variants.get(variant_name=variant_name)
                self.stdout.write(f"Found variant {variant_name}:")
                
                if test.test_type == 'thumbnail':
                    self.stdout.write(f"  Thumbnail: {variant.thumbnail_url}")
                elif test.test_type == 'title':
                    self.stdout.write(f"  Title: {variant.title}")
                elif test.test_type == 'description':
                    self.stdout.write(f"  Description: {variant.description[:100]}...")
                elif test.test_type == 'combined':
                    self.stdout.write(f"  Thumbnail: {variant.thumbnail_url}")
                    self.stdout.write(f"  Title: {variant.title}")
                
            except TestVariant.DoesNotExist:
                raise CommandError(f"Variant '{variant_name}' not found for test {test_id}")
            
            # Apply the variant
            self.stdout.write(self.style.WARNING(f"\nApplying variant {variant_name} to YouTube video {test.video_id}..."))
            
            scheduler = VariantScheduler(user=test.creator)
            success, error = scheduler.apply_variant(test_id, variant.id)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f"✓ Successfully applied variant {variant_name} to video!"))
                self.stdout.write(f"  Video ID: {test.video_id}")
                self.stdout.write(f"  Applied at: {variant.applied_at}")
            else:
                raise CommandError(f"Failed to apply variant: {error}")
                
        except ABTest.DoesNotExist:
            raise CommandError(f"Test with ID {test_id} not found")
        except Exception as e:
            raise CommandError(f"Error: {str(e)}")
