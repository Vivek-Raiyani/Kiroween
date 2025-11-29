from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import Mock, patch, MagicMock
from integrations.models import Integration
from integrations.google_drive import GoogleDriveService
from files.models import DriveFile
from datetime import datetime, timedelta
from django.utils import timezone
import io

User = get_user_model()


class FileUploadViewTests(TestCase):
    """Tests for file upload functionality."""
    
    def setUp(self):
        """Set up test users and authentication."""
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
        
        # Create manager
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        self.client = Client()
    
    def test_file_upload_requires_authentication(self):
        """Test that file upload requires user to be logged in."""
        response = self.client.get(reverse('file_upload'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_file_upload_requires_drive_connection(self):
        """Test that file upload requires Drive to be connected."""
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('file_upload'))
        
        # Should redirect to file list with error message
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('file_list'))
    
    @patch('integrations.google_drive.GoogleDriveService.get_credentials')
    @patch('integrations.google_drive.GoogleDriveService.get_storage_quota')
    def test_file_upload_displays_quota_info(self, mock_quota, mock_creds):
        """Test that file upload page displays quota information."""
        # Mock authentication
        mock_creds.return_value = Mock()
        
        # Mock quota
        mock_quota.return_value = {
            'limit': 15 * 1024**3,  # 15GB
            'usage': 5 * 1024**3,   # 5GB
            'available': 10 * 1024**3  # 10GB
        }
        
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('file_upload'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('quota_info', response.context)
        self.assertAlmostEqual(response.context['quota_info']['usage_gb'], 5.0, places=1)
        self.assertAlmostEqual(response.context['quota_info']['available_gb'], 10.0, places=1)
    
    @patch('integrations.google_drive.GoogleDriveService.get_credentials')
    @patch('integrations.google_drive.GoogleDriveService.validate_file_size')
    @patch('integrations.google_drive.GoogleDriveService.upload_file')
    def test_file_upload_success(self, mock_upload, mock_validate, mock_creds):
        """Test successful file upload."""
        # Mock authentication
        mock_creds.return_value = Mock()
        
        # Mock validation
        mock_validate.return_value = (True, "File size is within quota")
        
        # Mock upload
        mock_upload.return_value = {
            'id': 'test_file_id',
            'name': 'test.txt',
            'mimeType': 'text/plain',
            'size': '1024',
            'modifiedTime': '2024-01-01T12:00:00Z',
            'webViewLink': 'https://drive.google.com/file/test'
        }
        
        self.client.login(username='editor', password='testpass123')
        
        # Create test file
        test_file = SimpleUploadedFile(
            "test.txt",
            b"test content",
            content_type="text/plain"
        )
        
        response = self.client.post(reverse('file_upload'), {
            'file': test_file
        })
        
        # Should redirect to file list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('file_list'))
        
        # Verify file was cached
        self.assertTrue(DriveFile.objects.filter(file_id='test_file_id').exists())
    
    @patch('integrations.google_drive.GoogleDriveService.get_credentials')
    @patch('integrations.google_drive.GoogleDriveService.validate_file_size')
    def test_file_upload_quota_exceeded(self, mock_validate, mock_creds):
        """Test file upload when quota is exceeded."""
        # Mock authentication
        mock_creds.return_value = Mock()
        
        # Mock validation failure
        mock_validate.return_value = (False, "File size exceeds available Drive storage")
        
        self.client.login(username='editor', password='testpass123')
        
        # Create test file
        test_file = SimpleUploadedFile(
            "large_file.txt",
            b"x" * (100 * 1024 * 1024),  # 100MB
            content_type="text/plain"
        )
        
        response = self.client.post(reverse('file_upload'), {
            'file': test_file
        })
        
        # Should redirect back to upload page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('file_upload'))
    
    @patch('integrations.google_drive.GoogleDriveService.get_credentials')
    @patch('integrations.google_drive.GoogleDriveService.validate_file_size')
    def test_file_upload_no_file_selected(self, mock_validate, mock_creds):
        """Test file upload when no file is selected."""
        # Mock authentication
        mock_creds.return_value = Mock()
        
        self.client.login(username='editor', password='testpass123')
        
        response = self.client.post(reverse('file_upload'), {})
        
        # Should redirect back to upload page with error
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('file_upload'))
    
    @patch('integrations.google_drive.GoogleDriveService.get_credentials')
    @patch('integrations.google_drive.GoogleDriveService.validate_file_size')
    @patch('integrations.google_drive.GoogleDriveService.upload_file')
    def test_file_upload_drive_api_error(self, mock_upload, mock_validate, mock_creds):
        """Test file upload when Drive API returns error."""
        # Mock authentication
        mock_creds.return_value = Mock()
        
        # Mock validation
        mock_validate.return_value = (True, "File size is within quota")
        
        # Mock upload failure
        mock_upload.return_value = None
        
        self.client.login(username='editor', password='testpass123')
        
        test_file = SimpleUploadedFile(
            "test.txt",
            b"test content",
            content_type="text/plain"
        )
        
        response = self.client.post(reverse('file_upload'), {
            'file': test_file
        })
        
        # Should stay on upload page (no redirect on error in current implementation)
        self.assertEqual(response.status_code, 200)


class GoogleDriveServiceQuotaTests(TestCase):
    """Tests for Google Drive quota checking functionality."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='creator'
        )
        self.service = GoogleDriveService(user=self.user)
    
    @patch('integrations.google_drive.GoogleDriveService.get_service')
    def test_get_storage_quota_success(self, mock_get_service):
        """Test successful quota retrieval."""
        # Mock Drive service
        mock_service = Mock()
        mock_about = Mock()
        mock_about.get.return_value.execute.return_value = {
            'storageQuota': {
                'limit': '16106127360',  # 15GB
                'usage': '5368709120'    # 5GB
            }
        }
        mock_service.about.return_value = mock_about
        mock_get_service.return_value = mock_service
        
        quota = self.service.get_storage_quota()
        
        self.assertIsNotNone(quota)
        self.assertEqual(quota['limit'], 16106127360)
        self.assertEqual(quota['usage'], 5368709120)
        self.assertEqual(quota['available'], 16106127360 - 5368709120)
    
    @patch('integrations.google_drive.GoogleDriveService.get_service')
    def test_get_storage_quota_no_service(self, mock_get_service):
        """Test quota retrieval when service is not available."""
        mock_get_service.return_value = None
        
        quota = self.service.get_storage_quota()
        
        self.assertIsNone(quota)
    
    @patch('integrations.google_drive.GoogleDriveService.get_storage_quota')
    def test_validate_file_size_within_quota(self, mock_quota):
        """Test file size validation when file fits in quota."""
        mock_quota.return_value = {
            'limit': 15 * 1024**3,
            'usage': 5 * 1024**3,
            'available': 10 * 1024**3
        }
        
        # Test with 1GB file
        is_valid, message = self.service.validate_file_size(1 * 1024**3)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "File size is within quota")
    
    @patch('integrations.google_drive.GoogleDriveService.get_storage_quota')
    def test_validate_file_size_exceeds_quota(self, mock_quota):
        """Test file size validation when file exceeds quota."""
        mock_quota.return_value = {
            'limit': 15 * 1024**3,
            'usage': 14 * 1024**3,
            'available': 1 * 1024**3
        }
        
        # Test with 2GB file (exceeds 1GB available)
        is_valid, message = self.service.validate_file_size(2 * 1024**3)
        
        self.assertFalse(is_valid)
        self.assertIn("exceeds available Drive storage", message)
    
    @patch('integrations.google_drive.GoogleDriveService.get_storage_quota')
    def test_validate_file_size_no_quota_info(self, mock_quota):
        """Test file size validation when quota info is unavailable."""
        mock_quota.return_value = None
        
        # Should allow upload with warning
        is_valid, message = self.service.validate_file_size(1 * 1024**3)
        
        self.assertTrue(is_valid)
        self.assertIn("Warning", message)
