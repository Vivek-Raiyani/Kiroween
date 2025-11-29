from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from unittest.mock import patch, MagicMock
from .models import Integration
from .google_drive import GoogleDriveService
from .youtube import YouTubeService

User = get_user_model()


class GoogleDriveServiceTest(TestCase):
    """Test cases for GoogleDriveService class."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testcreator',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        self.drive_service = GoogleDriveService(user=self.user)
    
    def test_encryption_decryption(self):
        """Test token encryption and decryption."""
        original_token = "test_access_token_12345"
        
        # Encrypt token
        encrypted = self.drive_service.encrypt_token(original_token)
        self.assertNotEqual(encrypted, original_token)
        
        # Decrypt token
        decrypted = self.drive_service.decrypt_token(encrypted)
        self.assertEqual(decrypted, original_token)
    
    def test_get_authorization_url(self):
        """Test OAuth authorization URL generation."""
        auth_url = self.drive_service.get_authorization_url()
        
        self.assertIn('accounts.google.com/o/oauth2/auth', auth_url)
        self.assertIn('client_id', auth_url)
        self.assertIn('scope', auth_url)
        self.assertIn('redirect_uri', auth_url)
    
    @patch('integrations.google_drive.requests.post')
    def test_authenticate_success(self, mock_post):
        """Test successful OAuth authentication."""
        # Mock the token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'access_token_123',
            'refresh_token': 'refresh_token_123',
            'expires_in': 3600,
            'scope': 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file'
        }
        mock_post.return_value = mock_response
        
        # Test authentication
        result = self.drive_service.authenticate("auth_code_123")
        
        self.assertTrue(result)
        
        # Check that integration was created
        integration = Integration.objects.get(
            user=self.user,
            service_type='google_drive'
        )
        self.assertIsNotNone(integration)
    
    def test_is_authenticated_no_integration(self):
        """Test authentication check when no integration exists."""
        result = self.drive_service.is_authenticated()
        self.assertFalse(result)
    
    def test_disconnect(self):
        """Test disconnecting Google Drive integration."""
        # Create an integration first
        Integration.objects.create(
            user=self.user,
            service_type='google_drive',
            access_token='encrypted_access_token',
            refresh_token='encrypted_refresh_token',
            expires_at='2024-12-31 23:59:59'
        )
        
        # Test disconnection
        result = self.drive_service.disconnect()
        
        self.assertTrue(result)
        
        # Check that integration was deleted
        self.assertFalse(
            Integration.objects.filter(
                user=self.user,
                service_type='google_drive'
            ).exists()
        )


class GoogleDriveViewsTest(TestCase):
    """Test cases for Google Drive OAuth views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.creator = User.objects.create_user(
            username='testcreator',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        self.manager = User.objects.create_user(
            username='testmanager',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
    
    def test_integrations_dashboard_creator_access(self):
        """Test that creators can access integrations dashboard."""
        self.client.login(username='testcreator', password='testpass123')
        
        response = self.client.get(reverse('integrations'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Google Drive')
        self.assertContains(response, 'YouTube')
    
    def test_integrations_dashboard_manager_denied(self):
        """Test that managers cannot access integrations dashboard."""
        self.client.login(username='testmanager', password='testpass123')
        
        response = self.client.get(reverse('integrations'))
        
        # Should be redirected to permission denied
        self.assertEqual(response.status_code, 302)
    
    def test_google_drive_connect_creator_access(self):
        """Test that creators can initiate Google Drive connection."""
        self.client.login(username='testcreator', password='testpass123')
        
        response = self.client.get(reverse('google_drive_connect'))
        
        # Should redirect to Google OAuth
        self.assertEqual(response.status_code, 302)
        self.assertIn('accounts.google.com', response.url)
    
    def test_google_drive_callback_success(self):
        """Test successful Google Drive OAuth callback."""
        self.client.login(username='testcreator', password='testpass123')
        
        with patch('integrations.views.GoogleDriveService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.authenticate.return_value = True
            mock_service_class.return_value = mock_service
            
            response = self.client.get(
                reverse('google_drive_callback'),
                {'code': 'test_auth_code'}
            )
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('integrations'))
    
    def test_google_drive_callback_error(self):
        """Test Google Drive OAuth callback with error."""
        self.client.login(username='testcreator', password='testpass123')
        
        response = self.client.get(
            reverse('google_drive_callback'),
            {'error': 'access_denied'}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('integrations'))
    
    def test_google_drive_disconnect(self):
        """Test disconnecting Google Drive integration."""
        self.client.login(username='testcreator', password='testpass123')
        
        with patch('integrations.views.GoogleDriveService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.disconnect.return_value = True
            mock_service_class.return_value = mock_service
            
            response = self.client.post(reverse('google_drive_disconnect'))
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('integrations'))
    
    def test_google_drive_status_ajax(self):
        """Test Google Drive status AJAX endpoint."""
        self.client.login(username='testcreator', password='testpass123')
        
        with patch('integrations.views.GoogleDriveService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.is_authenticated.return_value = True
            mock_service_class.return_value = mock_service
            
            response = self.client.get(reverse('google_drive_status'))
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['connected'], True)


class IntegrationModelTest(TestCase):
    """Test cases for Integration model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='creator'
        )
    
    def test_integration_creation(self):
        """Test creating an integration."""
        integration = Integration.objects.create(
            user=self.user,
            service_type='google_drive',
            access_token='encrypted_access_token',
            refresh_token='encrypted_refresh_token',
            expires_at='2024-12-31 23:59:59'
        )
        
        self.assertEqual(integration.user, self.user)
        self.assertEqual(integration.service_type, 'google_drive')
        self.assertIsNotNone(integration.created_at)
    
    def test_integration_str_representation(self):
        """Test string representation of integration."""
        integration = Integration.objects.create(
            user=self.user,
            service_type='google_drive',
            access_token='encrypted_access_token',
            refresh_token='encrypted_refresh_token',
            expires_at='2024-12-31 23:59:59'
        )
        
        expected = f"{self.user.username} - Google Drive"
        self.assertEqual(str(integration), expected)
    
    def test_unique_constraint(self):
        """Test that user can only have one integration per service type."""
        # Create first integration
        Integration.objects.create(
            user=self.user,
            service_type='google_drive',
            access_token='encrypted_access_token_1',
            refresh_token='encrypted_refresh_token_1',
            expires_at='2024-12-31 23:59:59'
        )
        
        # Try to create duplicate - should update existing
        integration2, created = Integration.objects.update_or_create(
            user=self.user,
            service_type='google_drive',
            defaults={
                'access_token': 'encrypted_access_token_2',
                'refresh_token': 'encrypted_refresh_token_2',
                'expires_at': '2024-12-31 23:59:59'
            }
        )
        
        self.assertFalse(created)  # Should be updated, not created
        self.assertEqual(integration2.access_token, 'encrypted_access_token_2')


class YouTubeServiceTest(TestCase):
    """Test cases for YouTubeService class."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testcreator',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        self.youtube_service = YouTubeService(user=self.user)
    
    def test_encryption_decryption(self):
        """Test token encryption and decryption."""
        original_token = "test_youtube_token_12345"
        
        # Encrypt token
        encrypted = self.youtube_service.encrypt_token(original_token)
        self.assertNotEqual(encrypted, original_token)
        
        # Decrypt token
        decrypted = self.youtube_service.decrypt_token(encrypted)
        self.assertEqual(decrypted, original_token)
    
    def test_get_authorization_url(self):
        """Test YouTube OAuth authorization URL generation."""
        auth_url = self.youtube_service.get_authorization_url()
        
        self.assertIn('accounts.google.com/o/oauth2/auth', auth_url)
        self.assertIn('client_id', auth_url)
        self.assertIn('scope', auth_url)
        self.assertIn('youtube', auth_url)
    
    @patch('integrations.youtube.requests.post')
    def test_authenticate_success(self, mock_post):
        """Test successful YouTube OAuth authentication."""
        # Mock the token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'youtube_access_token_123',
            'refresh_token': 'youtube_refresh_token_123',
            'expires_in': 3600,
            'scope': 'https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.upload'
        }
        mock_post.return_value = mock_response
        
        # Test authentication
        result = self.youtube_service.authenticate("auth_code_123")
        
        self.assertTrue(result)
        
        # Check that integration was created
        integration = Integration.objects.get(
            user=self.user,
            service_type='youtube'
        )
        self.assertIsNotNone(integration)
    
    def test_is_authenticated_no_integration(self):
        """Test authentication check when no YouTube integration exists."""
        result = self.youtube_service.is_authenticated()
        self.assertFalse(result)
    
    @patch('integrations.youtube.build')
    def test_get_channel_info_success(self, mock_build):
        """Test successful channel information retrieval."""
        # Mock the YouTube service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Mock channel response
        mock_response = {
            'items': [{
                'id': 'UC123456789',
                'snippet': {
                    'title': 'Test Channel',
                    'description': 'Test Description',
                    'thumbnails': {'default': {'url': 'http://example.com/thumb.jpg'}},
                    'customUrl': '@testchannel',
                    'publishedAt': '2020-01-01T00:00:00Z'
                },
                'statistics': {
                    'subscriberCount': '1000',
                    'videoCount': '50',
                    'viewCount': '100000'
                }
            }]
        }
        
        mock_service.channels().list().execute.return_value = mock_response
        
        # Mock credentials
        with patch.object(self.youtube_service, 'get_credentials') as mock_get_creds:
            mock_get_creds.return_value = MagicMock()
            
            channel_info = self.youtube_service.get_channel_info()
            
            self.assertIsNotNone(channel_info)
            self.assertEqual(channel_info['title'], 'Test Channel')
            self.assertEqual(channel_info['subscriber_count'], '1000')
    
    def test_disconnect(self):
        """Test disconnecting YouTube integration."""
        # Create an integration first
        Integration.objects.create(
            user=self.user,
            service_type='youtube',
            access_token='encrypted_access_token',
            refresh_token='encrypted_refresh_token',
            expires_at='2024-12-31 23:59:59'
        )
        
        # Test disconnection
        result = self.youtube_service.disconnect()
        
        self.assertTrue(result)
        
        # Check that integration was deleted
        self.assertFalse(
            Integration.objects.filter(
                user=self.user,
                service_type='youtube'
            ).exists()
        )


class YouTubeViewsTest(TestCase):
    """Test cases for YouTube OAuth views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.creator = User.objects.create_user(
            username='testcreator',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        self.manager = User.objects.create_user(
            username='testmanager',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
    
    def test_youtube_connect_creator_access(self):
        """Test that creators can initiate YouTube connection."""
        self.client.login(username='testcreator', password='testpass123')
        
        response = self.client.get(reverse('youtube_connect'))
        
        # Should redirect to Google OAuth
        self.assertEqual(response.status_code, 302)
        self.assertIn('accounts.google.com', response.url)
    
    def test_youtube_connect_manager_denied(self):
        """Test that managers cannot initiate YouTube connection."""
        self.client.login(username='testmanager', password='testpass123')
        
        response = self.client.get(reverse('youtube_connect'))
        
        # Should be redirected to permission denied
        self.assertEqual(response.status_code, 302)
    
    def test_youtube_callback_success(self):
        """Test successful YouTube OAuth callback."""
        self.client.login(username='testcreator', password='testpass123')
        
        with patch('integrations.views.YouTubeService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.authenticate.return_value = True
            mock_service_class.return_value = mock_service
            
            response = self.client.get(
                reverse('youtube_callback'),
                {'code': 'test_auth_code'}
            )
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('integrations'))
    
    def test_youtube_callback_error(self):
        """Test YouTube OAuth callback with error."""
        self.client.login(username='testcreator', password='testpass123')
        
        response = self.client.get(
            reverse('youtube_callback'),
            {'error': 'access_denied'}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('integrations'))
    
    def test_youtube_disconnect(self):
        """Test disconnecting YouTube integration."""
        self.client.login(username='testcreator', password='testpass123')
        
        with patch('integrations.views.YouTubeService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.disconnect.return_value = True
            mock_service_class.return_value = mock_service
            
            response = self.client.post(reverse('youtube_disconnect'))
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('integrations'))
    
    def test_youtube_status_ajax(self):
        """Test YouTube status AJAX endpoint."""
        self.client.login(username='testcreator', password='testpass123')
        
        with patch('integrations.views.YouTubeService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.is_authenticated.return_value = True
            mock_service.get_channel_info.return_value = {
                'title': 'Test Channel',
                'subscriber_count': '1000'
            }
            mock_service_class.return_value = mock_service
            
            response = self.client.get(reverse('youtube_status'))
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['connected'], True)
            self.assertIsNotNone(data['channel_info'])
