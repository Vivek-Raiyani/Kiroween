from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from files.models import DriveFile
from approvals.models import ApprovalRequest
from integrations.models import Integration


class DashboardViewTests(TestCase):
    """Tests for role-specific dashboard views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create creator
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        # Create manager
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        # Create editor
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
        
        # Create test files
        self.file1 = DriveFile.objects.create(
            file_id='file1',
            name='test_video1.mp4',
            mime_type='video/mp4',
            size=1024000,
            modified_time=timezone.now(),
            creator=self.creator
        )
        
        self.file2 = DriveFile.objects.create(
            file_id='file2',
            name='test_video2.mp4',
            mime_type='video/mp4',
            size=2048000,
            modified_time=timezone.now() - timedelta(days=1),
            creator=self.creator
        )
        
        # Create approval requests
        self.request1 = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.file1,
            description='Test request 1',
            status='pending'
        )
        
        self.request2 = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.file2,
            description='Test request 2',
            status='approved',
            reviewed_by=self.manager,
            reviewed_at=timezone.now()
        )
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_editor_dashboard_displays_correctly(self):
        """Test that editor dashboard shows correct data."""
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'editor')
        self.assertContains(response, 'Total Requests')
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Recent Files')
        
        # Check statistics
        self.assertEqual(response.context['total_requests'], 2)
        self.assertEqual(response.context['pending_requests_count'], 1)
        self.assertEqual(response.context['approved_requests'], 1)
    
    def test_manager_dashboard_displays_correctly(self):
        """Test that manager dashboard shows correct data."""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'manager')
        self.assertContains(response, 'Pending Approvals')
        self.assertContains(response, 'Team Activity')
        
        # Check statistics
        self.assertEqual(response.context['pending_approvals_count'], 1)
        self.assertEqual(response.context['total_approved'], 1)
        self.assertEqual(response.context['reviewed_by_me'], 1)
    
    def test_creator_dashboard_displays_correctly(self):
        """Test that creator dashboard shows correct data."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'creator')
        self.assertContains(response, 'Team Members')
        self.assertContains(response, 'Integration Status')
        self.assertContains(response, 'Platform Statistics')
        
        # Check statistics
        self.assertEqual(response.context['total_members'], 2)  # manager + editor
        self.assertEqual(response.context['managers_count'], 1)
        self.assertEqual(response.context['editors_count'], 1)
        self.assertEqual(response.context['total_files'], 2)
        self.assertEqual(response.context['pending_requests'], 1)
    
    def test_editor_dashboard_shows_recent_files(self):
        """Test that editor dashboard shows recent files."""
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        recent_files = response.context['recent_files']
        self.assertEqual(len(recent_files), 2)
        self.assertEqual(recent_files[0].name, 'test_video1.mp4')
    
    def test_manager_dashboard_shows_pending_approvals(self):
        """Test that manager dashboard shows pending approvals."""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        pending_approvals = response.context['pending_approvals']
        self.assertEqual(pending_approvals.count(), 1)
        self.assertEqual(pending_approvals[0].status, 'pending')
    
    def test_creator_dashboard_shows_integration_status(self):
        """Test that creator dashboard shows integration status."""
        # Create Drive integration
        Integration.objects.create(
            user=self.creator,
            service_type='google_drive',
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertTrue(response.context['drive_connected'])
        self.assertFalse(response.context['youtube_connected'])
    
    def test_dashboard_role_detection(self):
        """Test that dashboard correctly detects user role."""
        # Test editor
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['role'], 'editor')
        
        # Test manager
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['role'], 'manager')
        
        # Test creator
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['role'], 'creator')
    
    def test_editor_dashboard_upload_statistics(self):
        """Test that editor dashboard shows correct upload statistics."""
        # Create additional requests with different statuses
        ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.file1,
            description='Rejected request',
            status='rejected',
            reviewed_by=self.manager,
            reviewed_at=timezone.now(),
            rejection_reason='Not good enough'
        )
        
        ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.file2,
            description='Uploaded request',
            status='uploaded',
            reviewed_by=self.manager,
            reviewed_at=timezone.now(),
            youtube_video_id='abc123'
        )
        
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.context['total_requests'], 4)
        self.assertEqual(response.context['pending_requests_count'], 1)
        self.assertEqual(response.context['approved_requests'], 1)
        self.assertEqual(response.context['rejected_requests'], 1)
        self.assertEqual(response.context['uploaded_requests'], 1)
    
    def test_creator_dashboard_recent_activity_count(self):
        """Test that creator dashboard shows recent activity count."""
        # Create old request (more than 7 days ago)
        old_request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.file1,
            description='Old request',
            status='approved'
        )
        old_request.created_at = timezone.now() - timedelta(days=10)
        old_request.save()
        
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Should only count requests from last 7 days
        self.assertEqual(response.context['recent_activity_count'], 2)
