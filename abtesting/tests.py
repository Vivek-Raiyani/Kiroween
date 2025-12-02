from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import ABTest, TestVariant, TestResult, TestLog
from .metrics_collector import MetricsCollector
from .test_engine import ABTestEngine

User = get_user_model()


class MetricsCollectorTestCase(TestCase):
    """Test cases for MetricsCollector service."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testcreator',
            email='test@example.com',
            password='testpass123',
            role='creator'
        )
        
        # Create a test using the engine
        engine = ABTestEngine(user=self.user)
        self.test, error = engine.create_test(
            video_id='test_video_123',
            video_title='Test Video',
            test_type='thumbnail',
            variants_data=[
                {'name': 'A', 'thumbnail_url': 'https://example.com/thumb_a.jpg'},
                {'name': 'B', 'thumbnail_url': 'https://example.com/thumb_b.jpg'}
            ],
            duration_hours=48,
            rotation_frequency_hours=6
        )
        
        self.assertIsNotNone(self.test)
        self.assertIsNone(error)
        
        # Start the test
        success, error = engine.start_test(self.test.id)
        self.assertTrue(success)
        
        # Get variants
        self.variant_a = self.test.variants.get(variant_name='A')
        self.variant_b = self.test.variants.get(variant_name='B')
    
    def test_calculate_variant_ctr_with_valid_data(self):
        """Test CTR calculation with valid impressions and clicks."""
        collector = MetricsCollector(user=self.user)
        
        # Test with 1000 impressions and 50 clicks (5% CTR)
        ctr = collector.calculate_variant_ctr(1000, 50)
        self.assertEqual(ctr, 5.0)
        
        # Test with 500 impressions and 25 clicks (5% CTR)
        ctr = collector.calculate_variant_ctr(500, 25)
        self.assertEqual(ctr, 5.0)
        
        # Test with 100 impressions and 10 clicks (10% CTR)
        ctr = collector.calculate_variant_ctr(100, 10)
        self.assertEqual(ctr, 10.0)
    
    def test_calculate_variant_ctr_with_zero_impressions(self):
        """Test CTR calculation with zero impressions."""
        collector = MetricsCollector(user=self.user)
        
        # Should return 0 when impressions is 0
        ctr = collector.calculate_variant_ctr(0, 50)
        self.assertEqual(ctr, 0.0)
    
    def test_calculate_variant_ctr_with_variant_instance(self):
        """Test CTR calculation with TestVariant instance."""
        collector = MetricsCollector(user=self.user)
        
        # Set variant metrics
        self.variant_a.impressions = 1000
        self.variant_a.clicks = 75
        self.variant_a.save()
        
        # Calculate CTR from variant instance
        ctr = collector.calculate_variant_ctr(self.variant_a)
        self.assertEqual(ctr, 7.5)
    
    def test_update_variant_stats_with_valid_metrics(self):
        """Test updating variant statistics with valid metrics."""
        collector = MetricsCollector(user=self.user)
        
        metrics = {
            'impressions': 1000,
            'clicks': 50,
            'views': 45,
            'ctr': 5.0
        }
        
        success, error = collector.update_variant_stats(self.variant_a.id, metrics)
        
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Verify variant was updated
        self.variant_a.refresh_from_db()
        self.assertEqual(self.variant_a.impressions, 1000)
        self.assertEqual(self.variant_a.clicks, 50)
        self.assertEqual(self.variant_a.views, 45)
        self.assertEqual(self.variant_a.ctr, 5.0)
        
        # Verify TestResult records were created
        results = TestResult.objects.filter(variant=self.variant_a)
        self.assertEqual(results.count(), 4)  # One for each metric type
    
    def test_update_variant_stats_with_missing_metrics(self):
        """Test updating variant statistics with missing required metrics."""
        collector = MetricsCollector(user=self.user)
        
        # Missing 'ctr' key
        metrics = {
            'impressions': 1000,
            'clicks': 50,
            'views': 45
        }
        
        success, error = collector.update_variant_stats(self.variant_a.id, metrics)
        
        self.assertFalse(success)
        self.assertIn("Missing required metric", error)
    
    def test_update_variant_stats_with_invalid_variant_id(self):
        """Test updating variant statistics with invalid variant ID."""
        collector = MetricsCollector(user=self.user)
        
        metrics = {
            'impressions': 1000,
            'clicks': 50,
            'views': 45,
            'ctr': 5.0
        }
        
        success, error = collector.update_variant_stats(99999, metrics)
        
        self.assertFalse(success)
        self.assertEqual(error, "Variant not found")
    
    def test_collect_variant_metrics_with_inactive_test(self):
        """Test collecting metrics for a test that is not active."""
        collector = MetricsCollector(user=self.user)
        
        # Create a draft test
        engine = ABTestEngine(user=self.user)
        draft_test, error = engine.create_test(
            video_id='draft_video_123',
            video_title='Draft Video',
            test_type='title',
            variants_data=[
                {'name': 'A', 'title': 'Title A'},
                {'name': 'B', 'title': 'Title B'}
            ],
            duration_hours=24,
            rotation_frequency_hours=6
        )
        
        # Try to collect metrics for draft test
        metrics, error = collector.collect_variant_metrics(draft_test.id)
        
        self.assertIsNone(metrics)
        self.assertIn("Cannot collect metrics for test with status 'draft'", error)
    
    def test_calculate_variant_ctr_with_invalid_inputs(self):
        """Test CTR calculation with invalid input types."""
        collector = MetricsCollector(user=self.user)
        
        # Test with string inputs
        ctr = collector.calculate_variant_ctr("invalid", "invalid")
        self.assertEqual(ctr, 0.0)
        
        # Test with None inputs
        ctr = collector.calculate_variant_ctr(None, None)
        self.assertEqual(ctr, 0.0)



class CombinedTestCase(TestCase):
    """Test cases for combined A/B testing functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testcreator',
            email='test@example.com',
            password='testpass123',
            role='creator'
        )
    
    def test_create_combined_test_with_valid_data(self):
        """Test creating a combined test with both thumbnail and title."""
        engine = ABTestEngine(user=self.user)
        
        test, error = engine.create_test(
            video_id='combined_test_123',
            video_title='Combined Test Video',
            test_type='combined',
            variants_data=[
                {
                    'name': 'A',
                    'thumbnail_url': 'https://example.com/thumb_a.jpg',
                    'title': 'Amazing Video Title A'
                },
                {
                    'name': 'B',
                    'thumbnail_url': 'https://example.com/thumb_b.jpg',
                    'title': 'Amazing Video Title B'
                }
            ],
            duration_hours=48,
            rotation_frequency_hours=6
        )
        
        self.assertIsNotNone(test)
        self.assertIsNone(error)
        self.assertEqual(test.test_type, 'combined')
        self.assertEqual(test.variants.count(), 2)
        
        # Verify both variants have thumbnail and title
        for variant in test.variants.all():
            self.assertIsNotNone(variant.thumbnail_url)
            self.assertIsNotNone(variant.title)
    
    def test_create_combined_test_without_thumbnail(self):
        """Test creating a combined test without thumbnail should fail."""
        engine = ABTestEngine(user=self.user)
        
        test, error = engine.create_test(
            video_id='combined_test_123',
            video_title='Combined Test Video',
            test_type='combined',
            variants_data=[
                {
                    'name': 'A',
                    'title': 'Amazing Video Title A'
                },
                {
                    'name': 'B',
                    'thumbnail_url': 'https://example.com/thumb_b.jpg',
                    'title': 'Amazing Video Title B'
                }
            ],
            duration_hours=48,
            rotation_frequency_hours=6
        )
        
        self.assertIsNone(test)
        self.assertIn("Combined test requires both thumbnail_url and title", error)
    
    def test_create_combined_test_without_title(self):
        """Test creating a combined test without title should fail."""
        engine = ABTestEngine(user=self.user)
        
        test, error = engine.create_test(
            video_id='combined_test_123',
            video_title='Combined Test Video',
            test_type='combined',
            variants_data=[
                {
                    'name': 'A',
                    'thumbnail_url': 'https://example.com/thumb_a.jpg',
                    'title': 'Amazing Video Title A'
                },
                {
                    'name': 'B',
                    'thumbnail_url': 'https://example.com/thumb_b.jpg'
                }
            ],
            duration_hours=48,
            rotation_frequency_hours=6
        )
        
        self.assertIsNone(test)
        self.assertIn("Combined test requires both thumbnail_url and title", error)
    
    def test_combined_test_element_impact_analysis(self):
        """Test element impact analysis for combined tests."""
        from abtesting.views import _analyze_combined_test_impact
        
        # Create a combined test
        engine = ABTestEngine(user=self.user)
        test, error = engine.create_test(
            video_id='combined_test_123',
            video_title='Combined Test Video',
            test_type='combined',
            variants_data=[
                {
                    'name': 'A',
                    'thumbnail_url': 'https://example.com/thumb_1.jpg',
                    'title': 'Title 1'
                },
                {
                    'name': 'B',
                    'thumbnail_url': 'https://example.com/thumb_2.jpg',
                    'title': 'Title 1'
                },
                {
                    'name': 'C',
                    'thumbnail_url': 'https://example.com/thumb_1.jpg',
                    'title': 'Title 2'
                }
            ],
            duration_hours=48,
            rotation_frequency_hours=6
        )
        
        self.assertIsNotNone(test)
        
        # Set different CTRs to simulate performance differences
        variants = list(test.variants.all().order_by('variant_name'))
        variants[0].ctr = 5.0  # A: thumb_1 + title_1
        variants[0].save()
        variants[1].ctr = 8.0  # B: thumb_2 + title_1
        variants[1].save()
        variants[2].ctr = 6.0  # C: thumb_1 + title_2
        variants[2].save()
        
        # Analyze impact
        impact = _analyze_combined_test_impact(test.variants.all())
        
        self.assertIsNotNone(impact)
        self.assertIn('thumbnail_impact', impact)
        self.assertIn('title_impact', impact)
        self.assertIn('primary_driver', impact)
        self.assertIn('analysis_message', impact)
        
        # Verify thumbnail impact calculation
        # thumb_1 appears in A (5.0) and C (6.0), avg = 5.5
        # thumb_2 appears in B (8.0), avg = 8.0
        self.assertEqual(len(impact['thumbnail_impact']), 2)
        
        # Verify title impact calculation
        # title_1 appears in A (5.0) and B (8.0), avg = 6.5
        # title_2 appears in C (6.0), avg = 6.0
        self.assertEqual(len(impact['title_impact']), 2)
    
    def test_combined_test_with_two_variants(self):
        """Test combined test with minimum number of variants (2)."""
        engine = ABTestEngine(user=self.user)
        
        test, error = engine.create_test(
            video_id='combined_test_123',
            video_title='Combined Test Video',
            test_type='combined',
            variants_data=[
                {
                    'name': 'A',
                    'thumbnail_url': 'https://example.com/thumb_a.jpg',
                    'title': 'Title A'
                },
                {
                    'name': 'B',
                    'thumbnail_url': 'https://example.com/thumb_b.jpg',
                    'title': 'Title B'
                }
            ],
            duration_hours=48,
            rotation_frequency_hours=6
        )
        
        self.assertIsNotNone(test)
        self.assertIsNone(error)
        self.assertEqual(test.variants.count(), 2)
    
    def test_combined_test_with_three_variants(self):
        """Test combined test with maximum number of variants (3)."""
        engine = ABTestEngine(user=self.user)
        
        test, error = engine.create_test(
            video_id='combined_test_123',
            video_title='Combined Test Video',
            test_type='combined',
            variants_data=[
                {
                    'name': 'A',
                    'thumbnail_url': 'https://example.com/thumb_a.jpg',
                    'title': 'Title A'
                },
                {
                    'name': 'B',
                    'thumbnail_url': 'https://example.com/thumb_b.jpg',
                    'title': 'Title B'
                },
                {
                    'name': 'C',
                    'thumbnail_url': 'https://example.com/thumb_c.jpg',
                    'title': 'Title C'
                }
            ],
            duration_hours=48,
            rotation_frequency_hours=6
        )
        
        self.assertIsNotNone(test)
        self.assertIsNone(error)
        self.assertEqual(test.variants.count(), 3)
