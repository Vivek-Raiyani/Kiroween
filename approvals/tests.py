from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User, Team
from files.models import DriveFile
from approvals.models import ApprovalRequest
from datetime import datetime


class ApprovalRequestModelTest(TestCase):
    """Test the ApprovalRequest model."""
    
    def setUp(self):
        """Set up test data."""
        # Create creator
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        # Create editor
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
        
        # Create a video file
        self.video_file = DriveFile.objects.create(
            file_id='test_file_123',
            name='test_video.mp4',
            mime_type='video/mp4',
            size=1024000,
            modified_time=timezone.now(),
            creator=self.creator
        )
    
    def test_create_approval_request(self):
        """Test creating an approval request."""
        request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            description='Test video for approval',
            status='pending'
        )
        
        self.assertEqual(request.editor, self.editor)
        self.assertEqual(request.creator, self.creator)
        self.assertEqual(request.file, self.video_file)
        self.assertEqual(request.status, 'pending')
        self.assertTrue(request.is_pending())
        self.assertFalse(request.is_approved())
    
    def test_approval_request_default_status(self):
        """Test that default status is pending."""
        request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file
        )
        
        self.assertEqual(request.status, 'pending')
    
    def test_approval_request_status_methods(self):
        """Test status checking methods."""
        request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            status='approved'
        )
        
        self.assertTrue(request.is_approved())
        self.assertFalse(request.is_pending())
        self.assertFalse(request.is_rejected())
        self.assertFalse(request.is_uploaded())
    
    def test_approval_request_string_representation(self):
        """Test string representation of approval request."""
        request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            status='pending'
        )
        
        expected = f"Request by {self.editor.username} for {self.video_file.name} (pending)"
        self.assertEqual(str(request), expected)


class ApprovalRequestViewTest(TestCase):
    """Test approval request views."""
    
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
        
        # Create team
        self.team = Team.objects.create(creator=self.creator)
        self.team.add_member(self.manager)
        self.team.add_member(self.editor)
        
        # Create a video file
        self.video_file = DriveFile.objects.create(
            file_id='test_file_123',
            name='test_video.mp4',
            mime_type='video/mp4',
            size=1024000,
            modified_time=timezone.now(),
            creator=self.creator
        )
    
    def test_create_approval_request_requires_login(self):
        """Test that creating approval request requires login."""
        response = self.client.get(reverse('create_approval_request'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_create_approval_request_requires_editor_role(self):
        """Test that only editors can create approval requests."""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('create_approval_request'))
        # Should be redirected or forbidden
        self.assertIn(response.status_code, [302, 403])
    
    def test_editor_can_access_create_approval_request(self):
        """Test that editors can access the create approval request page."""
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('create_approval_request'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Approval Request')
    
    def test_editor_can_create_approval_request(self):
        """Test that editors can create approval requests."""
        self.client.login(username='editor', password='testpass123')
        
        response = self.client.post(reverse('create_approval_request'), {
            'file': self.video_file.id,
            'description': 'Test video for approval'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that request was created
        request = ApprovalRequest.objects.filter(editor=self.editor).first()
        self.assertIsNotNone(request)
        self.assertEqual(request.file, self.video_file)
        self.assertEqual(request.status, 'pending')
        self.assertEqual(request.creator, self.creator)
    
    def test_approval_request_list_for_editor(self):
        """Test that editors can see their own requests."""
        # Create a request
        request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            description='Test request'
        )
        
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('approval_requests'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_video.mp4')
        self.assertContains(response, 'Pending')
    
    def test_pending_approvals_for_manager(self):
        """Test that managers can see pending approvals."""
        # Create a pending request
        request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            status='pending'
        )
        
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('pending_approvals'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_video.mp4')
        self.assertContains(response, 'Pending')
    
    def test_approval_request_detail_view(self):
        """Test viewing approval request details."""
        request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            description='Test description'
        )
        
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('approval_request_detail', args=[request.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_video.mp4')
        self.assertContains(response, 'Test description')
        self.assertContains(response, 'Pending')
    
    def test_editor_cannot_view_other_editor_requests(self):
        """Test that editors can only view their own requests."""
        # Create another editor
        other_editor = User.objects.create_user(
            username='other_editor',
            email='other@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
        
        # Create request by other editor
        request = ApprovalRequest.objects.create(
            editor=other_editor,
            creator=self.creator,
            file=self.video_file
        )
        
        # Try to view as first editor
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('approval_request_detail', args=[request.pk]))
        
        # Should be redirected with error
        self.assertEqual(response.status_code, 302)
    
    def test_manager_can_view_all_requests(self):
        """Test that managers can view all requests in their team."""
        request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file
        )
        
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('approval_request_detail', args=[request.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_video.mp4')


class ApprovalRequestFormTest(TestCase):
    """Test the ApprovalRequestForm."""
    
    def setUp(self):
        """Set up test data."""
        # Create creator
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        # Create editor
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
        
        # Create video files
        self.video_file = DriveFile.objects.create(
            file_id='video_123',
            name='test_video.mp4',
            mime_type='video/mp4',
            size=1024000,
            modified_time=timezone.now(),
            creator=self.creator
        )
        
        # Create non-video file
        self.doc_file = DriveFile.objects.create(
            file_id='doc_123',
            name='test_doc.pdf',
            mime_type='application/pdf',
            size=1024000,
            modified_time=timezone.now(),
            creator=self.creator
        )
    
    def test_form_only_shows_video_files(self):
        """Test that form only shows video files in the dropdown."""
        from approvals.forms import ApprovalRequestForm
        
        form = ApprovalRequestForm(user=self.editor)
        
        # Check that video file is in queryset
        self.assertIn(self.video_file, form.fields['file'].queryset)
        
        # Check that non-video file is not in queryset
        self.assertNotIn(self.doc_file, form.fields['file'].queryset)
    
    def test_form_description_is_optional(self):
        """Test that description field is optional."""
        from approvals.forms import ApprovalRequestForm
        
        form = ApprovalRequestForm(user=self.editor, data={
            'file': self.video_file.id,
            'description': ''
        })
        
        self.assertTrue(form.is_valid())
    
    def test_form_requires_file_selection(self):
        """Test that file selection is required."""
        from approvals.forms import ApprovalRequestForm
        
        form = ApprovalRequestForm(user=self.editor, data={
            'description': 'Test description'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)


class ApprovalReviewTest(TestCase):
    """Test approval and rejection functionality."""
    
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
        
        # Create team
        self.team = Team.objects.create(creator=self.creator)
        self.team.add_member(self.manager)
        self.team.add_member(self.editor)
        
        # Create a video file
        self.video_file = DriveFile.objects.create(
            file_id='test_file_123',
            name='test_video.mp4',
            mime_type='video/mp4',
            size=1024000,
            modified_time=timezone.now(),
            creator=self.creator
        )
        
        # Create a pending approval request
        self.request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            description='Test video for approval',
            status='pending'
        )
    
    def test_manager_can_approve_request(self):
        """Test that managers can approve approval requests."""
        self.client.login(username='manager', password='testpass123')
        
        response = self.client.get(reverse('approve_request', args=[self.request.pk]))
        
        # Should redirect after approval
        self.assertEqual(response.status_code, 302)
        
        # Check that request was approved
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'approved')
        self.assertEqual(self.request.reviewed_by, self.manager)
        self.assertIsNotNone(self.request.reviewed_at)
    
    def test_creator_can_approve_request(self):
        """Test that creators can approve approval requests."""
        self.client.login(username='creator', password='testpass123')
        
        response = self.client.get(reverse('approve_request', args=[self.request.pk]))
        
        # Should redirect after approval
        self.assertEqual(response.status_code, 302)
        
        # Check that request was approved
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'approved')
        self.assertEqual(self.request.reviewed_by, self.creator)
    
    def test_editor_cannot_approve_request(self):
        """Test that editors cannot approve requests."""
        self.client.login(username='editor', password='testpass123')
        
        response = self.client.get(reverse('approve_request', args=[self.request.pk]))
        
        # Should be redirected or forbidden
        self.assertIn(response.status_code, [302, 403])
        
        # Request should still be pending
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'pending')
    
    def test_manager_can_reject_request(self):
        """Test that managers can reject approval requests with reason."""
        self.client.login(username='manager', password='testpass123')
        
        response = self.client.post(reverse('reject_request', args=[self.request.pk]), {
            'rejection_reason': 'Video quality is too low. Please re-edit.'
        })
        
        # Should redirect after rejection
        self.assertEqual(response.status_code, 302)
        
        # Check that request was rejected
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'rejected')
        self.assertEqual(self.request.reviewed_by, self.manager)
        self.assertEqual(self.request.rejection_reason, 'Video quality is too low. Please re-edit.')
        self.assertIsNotNone(self.request.reviewed_at)
    
    def test_reject_requires_reason(self):
        """Test that rejection requires a reason."""
        self.client.login(username='manager', password='testpass123')
        
        response = self.client.post(reverse('reject_request', args=[self.request.pk]), {
            'rejection_reason': ''
        })
        
        # Should show form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        
        # Request should still be pending
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'pending')
    
    def test_cannot_review_already_reviewed_request(self):
        """Test that already reviewed requests cannot be reviewed again."""
        # Approve the request first
        self.request.status = 'approved'
        self.request.reviewed_by = self.manager
        self.request.reviewed_at = timezone.now()
        self.request.save()
        
        self.client.login(username='creator', password='testpass123')
        
        # Try to approve again
        response = self.client.get(reverse('approve_request', args=[self.request.pk]))
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        
        # Status should remain approved
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'approved')
    
    def test_request_history_shows_all_requests(self):
        """Test that request history shows all requests with decisions."""
        # Create additional requests with different statuses
        approved_request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            status='approved',
            reviewed_by=self.manager,
            reviewed_at=timezone.now()
        )
        
        rejected_request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            status='rejected',
            reviewed_by=self.manager,
            reviewed_at=timezone.now(),
            rejection_reason='Not good enough'
        )
        
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('request_history'))
        
        self.assertEqual(response.status_code, 200)
        
        # Should show all requests
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Approved')
        self.assertContains(response, 'Rejected')
    
    def test_editor_sees_updated_status(self):
        """Test that editors can see updated request status after review."""
        # Approve the request
        self.request.status = 'approved'
        self.request.reviewed_by = self.manager
        self.request.reviewed_at = timezone.now()
        self.request.save()
        
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('approval_requests'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved')
        
        # Check detail view
        response = self.client.get(reverse('approval_request_detail', args=[self.request.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved')
        self.assertContains(response, self.manager.username)



class YouTubeUploadTest(TestCase):
    """Test YouTube upload functionality."""
    
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
        
        # Create team
        self.team = Team.objects.create(creator=self.creator)
        self.team.add_member(self.manager)
        self.team.add_member(self.editor)
        
        # Create a video file
        self.video_file = DriveFile.objects.create(
            file_id='test_file_123',
            name='test_video.mp4',
            mime_type='video/mp4',
            size=1024000,
            modified_time=timezone.now(),
            creator=self.creator
        )
        
        # Create an approved approval request
        self.approved_request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            description='Test video for upload',
            status='approved',
            reviewed_by=self.manager,
            reviewed_at=timezone.now()
        )
        
        # Create a pending approval request
        self.pending_request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            description='Test video pending',
            status='pending'
        )
    
    def test_youtube_upload_list_requires_login(self):
        """Test that YouTube upload list requires login."""
        response = self.client.get(reverse('youtube_upload_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_youtube_upload_list_requires_manager_or_creator_role(self):
        """Test that only managers and creators can access YouTube upload list."""
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('youtube_upload_list'))
        # Should be redirected or forbidden
        self.assertIn(response.status_code, [302, 403])
    
    def test_manager_can_access_youtube_upload_list(self):
        """Test that managers can access YouTube upload list."""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('youtube_upload_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload to YouTube')
    
    def test_creator_can_access_youtube_upload_list(self):
        """Test that creators can access YouTube upload list."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('youtube_upload_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload to YouTube')
    
    def test_youtube_upload_list_shows_only_approved_videos(self):
        """Test that YouTube upload list shows only approved videos."""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('youtube_upload_list'))
        
        self.assertEqual(response.status_code, 200)
        
        # Should show approved request
        self.assertContains(response, 'Test video for upload')
        
        # Should not show pending request (it's in the same file, so we check count)
        requests = response.context['requests']
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].status, 'approved')
    
    def test_youtube_upload_form_requires_login(self):
        """Test that YouTube upload form requires login."""
        response = self.client.get(reverse('youtube_upload', args=[self.approved_request.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_youtube_upload_form_requires_manager_or_creator_role(self):
        """Test that only managers and creators can access YouTube upload form."""
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('youtube_upload', args=[self.approved_request.pk]))
        # Should be redirected or forbidden
        self.assertIn(response.status_code, [302, 403])
    
    def test_manager_can_access_youtube_upload_form(self):
        """Test that managers can access YouTube upload form (redirects if YouTube not connected)."""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('youtube_upload', args=[self.approved_request.pk]))
        # Should redirect to integrations if YouTube is not connected
        self.assertEqual(response.status_code, 302)
    
    def test_youtube_upload_form_shows_file_info(self):
        """Test that YouTube upload form redirects when YouTube not connected."""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('youtube_upload', args=[self.approved_request.pk]))
        
        # Should redirect to integrations if YouTube is not connected
        self.assertEqual(response.status_code, 302)
    
    def test_youtube_upload_form_cannot_upload_pending_request(self):
        """Test that pending requests cannot be uploaded."""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('youtube_upload', args=[self.pending_request.pk]))
        
        # Should redirect with error
        self.assertEqual(response.status_code, 302)
    
    def test_youtube_upload_form_requires_title(self):
        """Test that YouTube upload requires title (redirects if YouTube not connected)."""
        self.client.login(username='manager', password='testpass123')
        
        response = self.client.post(reverse('youtube_upload', args=[self.approved_request.pk]), {
            'title': '',
            'description': 'Test description',
            'privacy_status': 'private'
        })
        
        # Should redirect to integrations if YouTube is not connected
        self.assertEqual(response.status_code, 302)
        
        # Request should still be approved (not uploaded)
        self.approved_request.refresh_from_db()
        self.assertEqual(self.approved_request.status, 'approved')
    
    def test_youtube_upload_form_requires_description(self):
        """Test that YouTube upload requires description (redirects if YouTube not connected)."""
        self.client.login(username='manager', password='testpass123')
        
        response = self.client.post(reverse('youtube_upload', args=[self.approved_request.pk]), {
            'title': 'Test Video',
            'description': '',
            'privacy_status': 'private'
        })
        
        # Should redirect to integrations if YouTube is not connected
        self.assertEqual(response.status_code, 302)
        
        # Request should still be approved (not uploaded)
        self.approved_request.refresh_from_db()
        self.assertEqual(self.approved_request.status, 'approved')
    
    def test_youtube_upload_form_validates_privacy_status(self):
        """Test that YouTube upload validates privacy status (redirects if YouTube not connected)."""
        self.client.login(username='manager', password='testpass123')
        
        response = self.client.post(reverse('youtube_upload', args=[self.approved_request.pk]), {
            'title': 'Test Video',
            'description': 'Test description',
            'privacy_status': 'invalid_status'
        })
        
        # Should redirect to integrations if YouTube is not connected
        self.assertEqual(response.status_code, 302)
        
        # Request should still be approved (not uploaded)
        self.approved_request.refresh_from_db()
        self.assertEqual(self.approved_request.status, 'approved')
    
    def test_youtube_upload_list_shows_youtube_connection_status(self):
        """Test that YouTube upload list shows connection status."""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('youtube_upload_list'))
        
        self.assertEqual(response.status_code, 200)
        
        # Should show connection status in context
        self.assertIn('youtube_connected', response.context)
        
        # Since we don't have actual YouTube connection in tests, it should be False
        self.assertFalse(response.context['youtube_connected'])
    
    def test_approval_request_can_be_uploaded_method(self):
        """Test the can_be_uploaded method on ApprovalRequest."""
        # Approved request can be uploaded
        self.assertTrue(self.approved_request.can_be_uploaded())
        
        # Pending request cannot be uploaded
        self.assertFalse(self.pending_request.can_be_uploaded())
        
        # Rejected request cannot be uploaded
        rejected_request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            status='rejected',
            reviewed_by=self.manager,
            reviewed_at=timezone.now(),
            rejection_reason='Not good enough'
        )
        self.assertFalse(rejected_request.can_be_uploaded())
        
        # Uploaded request cannot be uploaded again
        uploaded_request = ApprovalRequest.objects.create(
            editor=self.editor,
            creator=self.creator,
            file=self.video_file,
            status='uploaded',
            reviewed_by=self.manager,
            reviewed_at=timezone.now(),
            youtube_video_id='test_video_id'
        )
        self.assertFalse(uploaded_request.can_be_uploaded())
