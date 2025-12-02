from django.test import TestCase
from datetime import datetime
from analytics.calculators import MetricsCalculator
from analytics.seo_analyzer import SEOAnalyzer
from analytics.posting_analyzer import PostingAnalyzer


class MetricsCalculatorTests(TestCase):
    """Tests for MetricsCalculator service."""
    
    def test_calculate_growth_rate_positive(self):
        """Test growth rate calculation with positive growth."""
        result = MetricsCalculator.calculate_growth_rate(100, 125)
        self.assertEqual(result, 25.0)
    
    def test_calculate_growth_rate_negative(self):
        """Test growth rate calculation with negative growth."""
        result = MetricsCalculator.calculate_growth_rate(100, 75)
        self.assertEqual(result, -25.0)
    
    def test_calculate_growth_rate_zero_old_value(self):
        """Test growth rate calculation with zero old value raises error."""
        with self.assertRaises(ValueError):
            MetricsCalculator.calculate_growth_rate(0, 100)
    
    def test_calculate_engagement_rate(self):
        """Test engagement rate calculation."""
        result = MetricsCalculator.calculate_engagement_rate(
            likes=100, comments=50, shares=25, views=1000
        )
        self.assertEqual(result, 17.5)
    
    def test_calculate_engagement_rate_zero_views(self):
        """Test engagement rate with zero views raises error."""
        with self.assertRaises(ValueError):
            MetricsCalculator.calculate_engagement_rate(10, 5, 2, 0)
    
    def test_calculate_ctr(self):
        """Test CTR calculation."""
        result = MetricsCalculator.calculate_ctr(clicks=50, impressions=1000)
        self.assertEqual(result, 5.0)
    
    def test_calculate_ctr_zero_impressions(self):
        """Test CTR with zero impressions raises error."""
        with self.assertRaises(ValueError):
            MetricsCalculator.calculate_ctr(10, 0)
    
    def test_aggregate_metrics(self):
        """Test metrics aggregation."""
        metrics = [
            {'views': 100, 'likes': 10},
            {'views': 200, 'likes': 20},
            {'views': 150, 'likes': 15}
        ]
        result = MetricsCalculator.aggregate_metrics(metrics)
        
        self.assertEqual(result['views']['sum'], 450)
        self.assertEqual(result['views']['average'], 150)
        self.assertEqual(result['views']['min'], 100)
        self.assertEqual(result['views']['max'], 200)
        self.assertEqual(result['likes']['sum'], 45)
    
    def test_aggregate_metrics_empty_list(self):
        """Test aggregation with empty list."""
        result = MetricsCalculator.aggregate_metrics([])
        self.assertEqual(result, {})


class SEOAnalyzerTests(TestCase):
    """Tests for SEOAnalyzer service."""
    
    def test_analyze_video_basic(self):
        """Test basic video analysis."""
        result = SEOAnalyzer.analyze_video(
            title="How to Learn Python Programming in 2024",
            description="Learn Python programming from scratch. This comprehensive guide covers variables, functions, and more. Visit https://example.com #Python #Programming",
            tags=["python", "programming", "tutorial", "coding", "learn python"]
        )
        
        self.assertIn('seo_score', result)
        self.assertGreaterEqual(result['seo_score'], 0)
        self.assertLessEqual(result['seo_score'], 100)
        self.assertIn('recommendations', result)
    
    def test_check_title_length_optimal(self):
        """Test title length check with optimal length."""
        is_optimal, msg = SEOAnalyzer.check_title_length("This is a good title with optimal length for SEO testing")
        self.assertTrue(is_optimal)
    
    def test_check_title_length_too_short(self):
        """Test title length check with short title."""
        is_optimal, msg = SEOAnalyzer.check_title_length("Short")
        self.assertFalse(is_optimal)
        self.assertIn("too short", msg)
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        keywords = SEOAnalyzer.extract_keywords("Learn Python Programming Tutorial")
        self.assertIn("learn", keywords)
        self.assertIn("python", keywords)
        self.assertIn("programming", keywords)
        self.assertNotIn("the", keywords)  # Stop word
    
    def test_check_description_structure(self):
        """Test description structure check."""
        description = "This is a great video.\n\nVisit https://example.com\n\n#Python #Tutorial"
        result = SEOAnalyzer.check_description_structure(description)
        
        self.assertTrue(result['has_links'])
        self.assertTrue(result['has_hashtags'])
        self.assertGreater(result['paragraph_count'], 1)
    
    def test_suggest_keywords(self):
        """Test keyword suggestions."""
        keywords = SEOAnalyzer.suggest_keywords(
            title="Python Programming Tutorial",
            description="Learn Python programming with this comprehensive tutorial on Python basics"
        )
        self.assertIsInstance(keywords, list)
        self.assertIn("python", keywords)


class PostingAnalyzerTests(TestCase):
    """Tests for PostingAnalyzer service."""
    
    def test_analyze_posting_patterns_empty(self):
        """Test posting pattern analysis with no videos."""
        result = PostingAnalyzer.analyze_posting_patterns([])
        self.assertEqual(result['sample_size'], 0)
        self.assertEqual(result['patterns'], {})
    
    def test_analyze_posting_patterns_with_data(self):
        """Test posting pattern analysis with video data."""
        videos = [
            {
                'published_at': datetime(2024, 1, 15, 14, 0),  # Monday 2 PM
                'views': 1000,
                'likes': 100,
                'comments': 50,
                'engagement_rate': 15.0
            },
            {
                'published_at': datetime(2024, 1, 16, 14, 0),  # Tuesday 2 PM
                'views': 1500,
                'likes': 150,
                'comments': 75,
                'engagement_rate': 15.0
            }
        ]
        result = PostingAnalyzer.analyze_posting_patterns(videos)
        
        self.assertEqual(result['sample_size'], 2)
        self.assertGreater(len(result['patterns']), 0)
        self.assertIsInstance(result['best_days'], list)
        self.assertIsInstance(result['best_hours'], list)
    
    def test_recommend_posting_times_insufficient_data(self):
        """Test recommendations with insufficient data (uses industry standards)."""
        videos = [
            {
                'published_at': datetime(2024, 1, 15, 14, 0),
                'views': 1000,
                'engagement_rate': 10.0
            }
        ]
        result = PostingAnalyzer.recommend_posting_times('channel123', videos)
        
        self.assertEqual(len(result), 3)
        for rec in result:
            self.assertIn('day_of_week', rec)
            self.assertIn('hour', rec)
            self.assertIn('expected_engagement', rec)
            self.assertIn('confidence_score', rec)
    
    def test_format_day_name(self):
        """Test day name formatting."""
        self.assertEqual(PostingAnalyzer.format_day_name(0), 'Monday')
        self.assertEqual(PostingAnalyzer.format_day_name(6), 'Sunday')
    
    def test_format_time(self):
        """Test time formatting."""
        self.assertEqual(PostingAnalyzer.format_time(0), '12:00 AM')
        self.assertEqual(PostingAnalyzer.format_time(12), '12:00 PM')
        self.assertEqual(PostingAnalyzer.format_time(14), '2:00 PM')
    
    def test_get_audience_activity_empty(self):
        """Test audience activity with no videos."""
        result = PostingAnalyzer.get_audience_activity('channel123', [])
        self.assertEqual(result['activity_by_day'], {})
        self.assertEqual(result['activity_by_hour'], {})
        self.assertEqual(result['peak_times'], [])



class CSVExporterTests(TestCase):
    """Tests for CSVExporter service."""
    
    def test_export_video_metrics_csv(self):
        """Test video metrics CSV export."""
        from analytics.exporters import CSVExporter
        from datetime import date
        
        video_id = 'test_video_123'
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        metrics_data = [
            {
                'date': '2024-01-01',
                'views': 1000,
                'watch_time': 500,
                'likes': 100,
                'comments': 50,
                'shares': 25,
                'ctr': 5.5,
                'engagement_rate': 17.5
            },
            {
                'date': '2024-01-02',
                'views': 1500,
                'watch_time': 750,
                'likes': 150,
                'comments': 75,
                'shares': 30,
                'ctr': 6.0,
                'engagement_rate': 17.0
            }
        ]
        
        response = CSVExporter.export_video_metrics(video_id, metrics_data, start_date, end_date)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('video_metrics_test_video_123', response['Content-Disposition'])
        
        # Verify content
        content = response.content.decode('utf-8')
        self.assertIn('Video ID', content)
        self.assertIn('Views', content)
        self.assertIn('test_video_123', content)
        self.assertIn('1000', content)
        self.assertIn('1500', content)
    
    def test_export_channel_metrics_csv(self):
        """Test channel metrics CSV export."""
        from analytics.exporters import CSVExporter
        from datetime import date
        
        channel_id = 'test_channel_123'
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        metrics_data = [
            {
                'date': '2024-01-01',
                'subscribers': 10000,
                'subscribers_gained': 100,
                'subscribers_lost': 10,
                'views': 5000,
                'watch_time': 2500,
                'avg_view_duration': 300
            },
            {
                'date': '2024-01-02',
                'subscribers': 10090,
                'subscribers_gained': 120,
                'subscribers_lost': 30,
                'views': 5500,
                'watch_time': 2750,
                'avg_view_duration': 310
            }
        ]
        
        response = CSVExporter.export_channel_metrics(channel_id, metrics_data, start_date, end_date)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('channel_metrics_test_channel_123', response['Content-Disposition'])
        
        # Verify content
        content = response.content.decode('utf-8')
        self.assertIn('Channel ID', content)
        self.assertIn('Subscribers', content)
        self.assertIn('test_channel_123', content)
        self.assertIn('10000', content)
    
    def test_export_test_results_csv(self):
        """Test A/B test results CSV export."""
        from analytics.exporters import CSVExporter
        
        test_data = {
            'test_id': 1,
            'video_id': 'test_video_123',
            'video_title': 'Test Video Title',
            'test_type': 'thumbnail',
            'status': 'completed',
            'start_date': '2024-01-01',
            'end_date': '2024-01-07',
            'duration_hours': 168,
            'variants': [
                {
                    'variant_name': 'A',
                    'impressions': 10000,
                    'clicks': 500,
                    'views': 450,
                    'ctr': 5.0,
                    'is_winner': False,
                    'thumbnail_url': 'https://example.com/thumb_a.jpg'
                },
                {
                    'variant_name': 'B',
                    'impressions': 10000,
                    'clicks': 600,
                    'views': 550,
                    'ctr': 6.0,
                    'is_winner': True,
                    'thumbnail_url': 'https://example.com/thumb_b.jpg'
                }
            ]
        }
        
        response = CSVExporter.export_test_results(1, test_data)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('abtest_results_1', response['Content-Disposition'])
        
        # Verify content
        content = response.content.decode('utf-8')
        self.assertIn('A/B Test Results', content)
        self.assertIn('Test Video Title', content)
        self.assertIn('Variant,A', content)
        self.assertIn('Variant,B', content)
        self.assertIn('10000', content)
        self.assertIn('Yes', content)  # Winner indicator


class PDFExporterTests(TestCase):
    """Tests for PDFExporter service."""
    
    def test_generate_analytics_report_pdf(self):
        """Test analytics report PDF generation."""
        from analytics.exporters import PDFExporter
        
        report_data = {
            'report_type': 'Video Analytics',
            'video_id': 'test_video_123',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'metrics': {
                'total_views': 50000,
                'total_watch_time': 25000,
                'engagement_rate': 15.5,
                'ctr': 5.5
            },
            'trend_data': {
                'dates': ['2024-01-01', '2024-01-02', '2024-01-03'],
                'views': [1000, 1500, 1200],
                'engagement': [15.0, 16.0, 15.5]
            }
        }
        
        response = PDFExporter.generate_analytics_report(report_data)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('analytics_report_', response['Content-Disposition'])
        
        # Verify PDF content exists
        content = response.content
        self.assertGreater(len(content), 0)
        # PDF files start with %PDF
        self.assertTrue(content.startswith(b'%PDF'))
    
    def test_generate_test_report_pdf(self):
        """Test A/B test report PDF generation."""
        from analytics.exporters import PDFExporter
        
        test_data = {
            'test_id': 1,
            'video_id': 'test_video_123',
            'video_title': 'Test Video Title',
            'test_type': 'thumbnail',
            'status': 'completed',
            'start_date': '2024-01-01',
            'end_date': '2024-01-07',
            'duration_hours': 168,
            'variants': [
                {
                    'variant_name': 'A',
                    'impressions': 10000,
                    'clicks': 500,
                    'views': 450,
                    'ctr': 5.0,
                    'is_winner': False,
                    'thumbnail_url': 'https://example.com/thumb_a.jpg'
                },
                {
                    'variant_name': 'B',
                    'impressions': 10000,
                    'clicks': 600,
                    'views': 550,
                    'ctr': 6.0,
                    'is_winner': True,
                    'thumbnail_url': 'https://example.com/thumb_b.jpg'
                }
            ]
        }
        
        response = PDFExporter.generate_test_report(test_data)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('abtest_report_1', response['Content-Disposition'])
        
        # Verify PDF content exists
        content = response.content
        self.assertGreater(len(content), 0)
        self.assertTrue(content.startswith(b'%PDF'))
    
    def test_add_charts_to_pdf(self):
        """Test chart generation for PDF reports."""
        from analytics.exporters import PDFExporter
        
        report_data = {
            'trend_data': {
                'dates': ['2024-01-01', '2024-01-02', '2024-01-03'],
                'views': [1000, 1500, 1200],
                'engagement': [15.0, 16.0, 15.5]
            }
        }
        
        charts = PDFExporter.add_charts_to_pdf(report_data)
        
        # Verify charts were generated
        self.assertIsInstance(charts, list)
        self.assertGreater(len(charts), 0)
        
        # Verify each chart is a BytesIO buffer
        for chart in charts:
            self.assertIsNotNone(chart)
            chart.seek(0)
            content = chart.read()
            self.assertGreater(len(content), 0)
