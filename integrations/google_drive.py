"""
Google Drive API service for handling OAuth authentication and file operations.
"""

import json
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from cryptography.fernet import Fernet
import base64
import os
from .models import Integration


class GoogleDriveService:
    """Service class for Google Drive API operations."""
    
    # Google Drive API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def __init__(self, user=None):
        """Initialize the service with optional user context."""
        self.user = user
        self._service = None
        self._credentials = None
    
    def get_encryption_key(self):
        """Get or create encryption key for token storage."""
        # Use Django's SECRET_KEY as base for encryption
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        return Fernet(key)
    
    def encrypt_token(self, token):
        """Encrypt a token for secure storage."""
        fernet = self.get_encryption_key()
        return fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token):
        """Decrypt a token from storage."""
        fernet = self.get_encryption_key()
        return fernet.decrypt(encrypted_token.encode()).decode()
    
    def get_oauth_flow(self, redirect_uri=None):
        """Create and return OAuth flow object."""
        if not redirect_uri:
            redirect_uri = settings.GOOGLE_DRIVE_REDIRECT_URI
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_DRIVE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_DRIVE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        flow.redirect_uri = redirect_uri
        return flow
    
    def get_authorization_url(self, redirect_uri=None):
        """Get the OAuth authorization URL."""
        flow = self.get_oauth_flow(redirect_uri)
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        return auth_url
    
    def authenticate(self, authorization_code, redirect_uri=None):
        """
        Exchange authorization code for tokens and store them.
        Returns tuple (success: bool, error_message: str or None)
        """
        try:
            # Directly exchange authorization code for tokens
            # This bypasses the Flow's strict scope checking
            token_response = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': authorization_code,
                    'client_id': settings.GOOGLE_DRIVE_CLIENT_ID,
                    'client_secret': settings.GOOGLE_DRIVE_CLIENT_SECRET,
                    'redirect_uri': redirect_uri or settings.GOOGLE_DRIVE_REDIRECT_URI,
                    'grant_type': 'authorization_code',
                },
                timeout=30
            )
            
            if token_response.status_code != 200:
                error_data = token_response.json() if token_response.text else {}
                error_msg = error_data.get('error_description', 'Token exchange failed')
                print(f"Token exchange failed: {token_response.text}")
                return False, f"Failed to connect Google Drive: {error_msg}"
            
            token_data = token_response.json()
            
            # Parse scopes from response
            granted_scopes = token_data.get('scope', '').split()
            
            # Verify we have at least one Drive scope
            drive_scopes = [s for s in granted_scopes if 'drive' in s]
            if not drive_scopes:
                print(f"No Drive scopes found in granted scopes: {granted_scopes}")
                return False, "Google Drive access was not granted. Please ensure you approve Drive permissions."
            
            print(f"Drive scopes found: {drive_scopes}")
            if len(granted_scopes) > len(drive_scopes):
                print(f"Additional scopes granted: {[s for s in granted_scopes if 'drive' not in s]}")
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 3600)
            expires_at = timezone.now() + timedelta(seconds=expires_in)
            
            # Encrypt tokens before storage
            encrypted_access_token = self.encrypt_token(token_data['access_token'])
            encrypted_refresh_token = None
            if token_data.get('refresh_token'):
                encrypted_refresh_token = self.encrypt_token(token_data['refresh_token'])
            
            # Store or update integration
            integration, created = Integration.objects.update_or_create(
                user=self.user,
                service_type='google_drive',
                defaults={
                    'access_token': encrypted_access_token,
                    'refresh_token': encrypted_refresh_token,
                    'expires_at': expires_at,
                }
            )
            
            print(f"Google Drive integration {'created' if created else 'updated'} successfully")
            return True, None
            
        except requests.exceptions.Timeout:
            error_msg = "Connection to Google timed out. Please check your internet connection and try again."
            print(f"OAuth authentication timeout")
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "Could not connect to Google. Please check your internet connection and try again."
            print(f"OAuth authentication connection error")
            return False, error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred while connecting Google Drive. Please try again."
            print(f"OAuth authentication error: {e}")
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def get_credentials(self):
        """
        Get valid credentials for the user.
        Returns tuple (credentials, error_message)
        """
        if not self.user:
            return None, "No user specified"
        
        try:
            integration = Integration.objects.get(
                user=self.user,
                service_type='google_drive'
            )
            
            # Decrypt tokens
            access_token = self.decrypt_token(integration.access_token)
            refresh_token = self.decrypt_token(integration.refresh_token)
            
            # Create credentials object
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_DRIVE_CLIENT_ID,
                client_secret=settings.GOOGLE_DRIVE_CLIENT_SECRET,
                scopes=self.SCOPES
            )
            
            # Check if token needs refresh
            if integration.is_expired():
                try:
                    credentials.refresh(Request())
                    
                    # Update stored tokens
                    integration.access_token = self.encrypt_token(credentials.token)
                    integration.expires_at = timezone.now() + timedelta(seconds=3600)  # 1 hour
                    integration.save()
                except Exception as refresh_error:
                    print(f"Token refresh failed: {refresh_error}")
                    return None, "Your Google Drive session has expired. Please reconnect your account."
            
            return credentials, None
            
        except Integration.DoesNotExist:
            return None, "Google Drive is not connected"
        except Exception as e:
            print(f"Error getting credentials: {e}")
            return None, f"Error accessing Google Drive credentials: {str(e)}"
    
    def get_service(self):
        """
        Get authenticated Google Drive service.
        Returns tuple (service, error_message)
        """
        if self._service:
            return self._service, None
        
        credentials, error = self.get_credentials()
        if not credentials:
            return None, error or "Could not get Google Drive credentials"
        
        try:
            self._service = build('drive', 'v3', credentials=credentials)
            return self._service, None
        except Exception as e:
            print(f"Error building Drive service: {e}")
            return None, f"Could not connect to Google Drive: {str(e)}"
    
    def is_authenticated(self):
        """Check if user has valid Google Drive authentication."""
        credentials, _ = self.get_credentials()
        return credentials is not None
    
    def disconnect(self):
        """Disconnect Google Drive integration for the user."""
        if not self.user:
            return False
        
        try:
            # NOTE: We do NOT revoke the token here because:
            # 1. If using the same OAuth client for Drive and YouTube, revoking one token
            #    will revoke ALL tokens for that client, breaking the other integration
            # 2. The user can revoke access from their Google Account settings if needed
            # 3. Just removing the integration from our database is sufficient for disconnect
            
            # Delete the integration record
            Integration.objects.filter(
                user=self.user,
                service_type='google_drive'
            ).delete()
            
            print("Google Drive integration disconnected successfully")
            return True
            
        except Exception as e:
            print(f"Error disconnecting Drive: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_files(self, query=None, page_token=None, page_size=100):
        """
        List files from Google Drive.
        
        Args:
            query: Search query string
            page_token: Token for pagination
            page_size: Number of files per page
            
        Returns:
            Tuple of (dict with 'files' list and 'nextPageToken', error_message)
        """
        service, error = self.get_service()
        if not service:
            return {'files': [], 'nextPageToken': None}, error
        
        try:
            # Build query parameters
            params = {
                'pageSize': page_size,
                'fields': 'nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, parents)',
                'orderBy': 'modifiedTime desc'
            }
            
            if query:
                params['q'] = f"name contains '{query}' and trashed=false"
            else:
                params['q'] = 'trashed=false'
            
            if page_token:
                params['pageToken'] = page_token
            
            # Execute API call
            results = service.files().list(**params).execute()
            
            return {
                'files': results.get('files', []),
                'nextPageToken': results.get('nextPageToken')
            }, None
            
        except HttpError as e:
            error_msg = f"Google Drive API error: {e.reason if hasattr(e, 'reason') else str(e)}"
            print(f"Drive API error: {e}")
            return {'files': [], 'nextPageToken': None}, error_msg
        except Exception as e:
            error_msg = f"Error retrieving files from Google Drive: {str(e)}"
            print(f"Error listing files: {e}")
            return {'files': [], 'nextPageToken': None}, error_msg
    
    def get_file(self, file_id):
        """Get file metadata by ID."""
        service, error = self.get_service()
        if not service:
            return None
        
        try:
            file = service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, modifiedTime, webViewLink, parents'
            ).execute()
            return file
        except HttpError as e:
            print(f"Drive API error getting file: {e}")
            return None
        except Exception as e:
            print(f"Error getting file: {e}")
            return None
    
    def upload_file(self, file_obj, filename, mime_type=None):
        """
        Upload a file to Google Drive.
        
        Args:
            file_obj: File object to upload
            filename: Name for the file
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (file metadata dict, error_message)
        """
        service, error = self.get_service()
        if not service:
            return None, error
        
        try:
            from googleapiclient.http import MediaIoBaseUpload
            
            file_metadata = {'name': filename}
            
            if mime_type:
                media = MediaIoBaseUpload(file_obj, mimetype=mime_type, resumable=True)
            else:
                media = MediaIoBaseUpload(file_obj, resumable=True)
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, size, modifiedTime, webViewLink'
            ).execute()
            
            return file, None
            
        except HttpError as e:
            if e.resp.status == 403:
                error_msg = "Insufficient permissions or storage quota exceeded. Please check your Google Drive storage."
            elif e.resp.status == 404:
                error_msg = "Google Drive folder not found. Please try again."
            elif e.resp.status == 429:
                error_msg = "Too many requests to Google Drive. Please wait a moment and try again."
            else:
                error_msg = f"Google Drive error: {e.reason if hasattr(e, 'reason') else 'Upload failed'}"
            print(f"Drive API error uploading file: {e}")
            return None, error_msg
        except Exception as e:
            error_msg = f"Failed to upload file: {str(e)}"
            print(f"Error uploading file: {e}")
            return None, error_msg
    
    def refresh_token(self):
        """Manually refresh the access token."""
        credentials = self.get_credentials()
        if credentials:
            try:
                credentials.refresh(Request())
                
                # Update stored token
                integration = Integration.objects.get(
                    user=self.user,
                    service_type='google_drive'
                )
                integration.access_token = self.encrypt_token(credentials.token)
                integration.expires_at = timezone.now() + timedelta(seconds=3600)
                integration.save()
                
                return True
            except Exception as e:
                print(f"Error refreshing token: {e}")
                return False
        return False
    
    def get_storage_quota(self):
        """
        Get storage quota information from Google Drive.
        
        Returns:
            Dict with 'limit', 'usage', and 'available' in bytes, or None if error
        """
        service, error = self.get_service()
        if not service:
            return None
        
        try:
            about = service.about().get(fields='storageQuota').execute()
            storage_quota = about.get('storageQuota', {})
            
            # Get quota values (all in bytes)
            limit = int(storage_quota.get('limit', 0))
            usage = int(storage_quota.get('usage', 0))
            
            # Calculate available space
            available = limit - usage if limit > 0 else float('inf')
            
            return {
                'limit': limit,
                'usage': usage,
                'available': available
            }
            
        except HttpError as e:
            print(f"Drive API error getting quota: {e}")
            return None
        except Exception as e:
            print(f"Error getting storage quota: {e}")
            return None
    
    def validate_file_size(self, file_size):
        """
        Validate if a file can be uploaded based on available quota.
        
        Args:
            file_size: Size of file in bytes
            
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        quota = self.get_storage_quota()
        
        if not quota:
            # If we can't get quota, allow upload but with warning
            return True, "Warning: Could not verify storage quota"
        
        available = quota['available']
        
        # Check if file fits in available space
        if file_size > available:
            # Format sizes for user-friendly message
            file_size_mb = file_size / (1024 * 1024)
            available_mb = available / (1024 * 1024)
            
            return False, f"File size ({file_size_mb:.1f} MB) exceeds available Drive storage ({available_mb:.1f} MB)"
        
        return True, "File size is within quota"