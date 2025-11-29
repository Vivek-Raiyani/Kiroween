"""
YouTube API service for handling OAuth authentication and video operations.
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


class YouTubeService:
    """Service class for YouTube API operations."""
    
    # YouTube API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/youtube.upload'
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
            redirect_uri = settings.YOUTUBE_REDIRECT_URI
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.YOUTUBE_CLIENT_ID,
                    "client_secret": settings.YOUTUBE_CLIENT_SECRET,
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
                    'client_id': settings.YOUTUBE_CLIENT_ID,
                    'client_secret': settings.YOUTUBE_CLIENT_SECRET,
                    'redirect_uri': redirect_uri or settings.YOUTUBE_REDIRECT_URI,
                    'grant_type': 'authorization_code',
                },
                timeout=30
            )
            
            if token_response.status_code != 200:
                error_data = token_response.json() if token_response.text else {}
                error_msg = error_data.get('error_description', 'Token exchange failed')
                print(f"Token exchange failed: {token_response.text}")
                return False, f"Failed to connect YouTube: {error_msg}"
            
            token_data = token_response.json()
            
            # Parse scopes from response
            granted_scopes = token_data.get('scope', '').split()
            
            # Verify we have at least one YouTube scope
            youtube_scopes = [s for s in granted_scopes if 'youtube' in s]
            if not youtube_scopes:
                print(f"No YouTube scopes found in granted scopes: {granted_scopes}")
                return False, "YouTube access was not granted. Please ensure you approve YouTube permissions."
            
            print(f"YouTube scopes found: {youtube_scopes}")
            if len(granted_scopes) > len(youtube_scopes):
                print(f"Additional scopes granted: {[s for s in granted_scopes if 'youtube' not in s]}")
            
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
                service_type='youtube',
                defaults={
                    'access_token': encrypted_access_token,
                    'refresh_token': encrypted_refresh_token,
                    'expires_at': expires_at,
                }
            )
            
            print(f"YouTube integration {'created' if created else 'updated'} successfully")
            return True, None
            
        except requests.exceptions.Timeout:
            error_msg = "Connection to Google timed out. Please check your internet connection and try again."
            print(f"YouTube OAuth authentication timeout")
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "Could not connect to Google. Please check your internet connection and try again."
            print(f"YouTube OAuth authentication connection error")
            return False, error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred while connecting YouTube. Please try again."
            print(f"YouTube OAuth authentication error: {e}")
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
                service_type='youtube'
            )
            
            # Decrypt tokens
            access_token = self.decrypt_token(integration.access_token)
            refresh_token = self.decrypt_token(integration.refresh_token) if integration.refresh_token else None
            
            # Create credentials object with flexible scopes
            # Include both YouTube and potentially Drive scopes that Google might have granted
            all_scopes = self.SCOPES + [
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file'
            ]
            
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.YOUTUBE_CLIENT_ID,
                client_secret=settings.YOUTUBE_CLIENT_SECRET,
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
                    return None, "Your YouTube session has expired. Please reconnect your account."
            
            return credentials, None
            
        except Integration.DoesNotExist:
            return None, "YouTube is not connected"
        except Exception as e:
            print(f"Error getting YouTube credentials: {e}")
            return None, f"Error accessing YouTube credentials: {str(e)}"
    
    def get_service(self):
        """
        Get authenticated YouTube service.
        Returns tuple (service, error_message)
        """
        if self._service:
            return self._service, None
        
        credentials, error = self.get_credentials()
        if not credentials:
            return None, error or "Could not get YouTube credentials"
        
        try:
            self._service = build('youtube', 'v3', credentials=credentials)
            return self._service, None
        except Exception as e:
            print(f"Error building YouTube service: {e}")
            return None, f"Could not connect to YouTube: {str(e)}"
    
    def is_authenticated(self):
        """Check if user has valid YouTube authentication."""
        credentials, _ = self.get_credentials()
        return credentials is not None
    
    def disconnect(self):
        """Disconnect YouTube integration for the user."""
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
                service_type='youtube'
            ).delete()
            
            print("YouTube integration disconnected successfully")
            return True
            
        except Exception as e:
            print(f"Error disconnecting YouTube: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_channel_info(self):
        """
        Get information about the authenticated user's YouTube channel.
        
        Returns:
            Tuple of (dict with channel information, error_message)
        """
        service, error = self.get_service()
        if not service:
            return None, error
        
        try:
            # Get channel information
            request = service.channels().list(
                part='snippet,statistics,contentDetails',
                mine=True
            )
            response = request.execute()
            
            if response.get('items'):
                channel = response['items'][0]
                return {
                    'id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description'],
                    'thumbnail': channel['snippet']['thumbnails'].get('default', {}).get('url'),
                    'subscriber_count': channel['statistics'].get('subscriberCount', '0'),
                    'video_count': channel['statistics'].get('videoCount', '0'),
                    'view_count': channel['statistics'].get('viewCount', '0'),
                    'custom_url': channel['snippet'].get('customUrl', ''),
                    'published_at': channel['snippet']['publishedAt']
                }, None
            
            return None, "No channel found for this account"
            
        except HttpError as e:
            error_msg = f"YouTube API error: {e.reason if hasattr(e, 'reason') else str(e)}"
            print(f"YouTube API error getting channel info: {e}")
            return None, error_msg
        except Exception as e:
            error_msg = f"Error getting channel info: {str(e)}"
            print(f"Error getting channel info: {e}")
            return None, error_msg
    
    def upload_video(self, file_obj, title, description, privacy_status='private', tags=None):
        """
        Upload a video to YouTube.
        
        Args:
            file_obj: File object to upload
            title: Video title
            description: Video description
            privacy_status: 'private', 'public', 'unlisted', or 'unlisted'
            tags: List of tags for the video
            
        Returns:
            Tuple of (video metadata dict, error_message)
        """
        service, error = self.get_service()
        if not service:
            return None, error or "YouTube is not connected"
        
        try:
            from googleapiclient.http import MediaIoBaseUpload
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags or [],
                    'categoryId': '22'  # People & Blogs category
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }
            
            # Create media upload object
            media = MediaIoBaseUpload(
                file_obj,
                mimetype='video/*',
                resumable=True,
                chunksize=1024*1024  # 1MB chunks
            )
            
            # Execute upload
            insert_request = service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = insert_request.execute()
            
            return {
                'id': response['id'],
                'title': response['snippet']['title'],
                'description': response['snippet']['description'],
                'privacy_status': response['status']['privacyStatus'],
                'upload_status': response['status']['uploadStatus'],
                'url': f"https://www.youtube.com/watch?v={response['id']}"
            }, None
            
        except HttpError as e:
            if e.resp.status == 403:
                error_msg = "YouTube upload quota exceeded or insufficient permissions. Please try again later or check your YouTube API quota."
            elif e.resp.status == 400:
                error_msg = "Invalid video format or metadata. Please check your video file and try again."
            elif e.resp.status == 401:
                error_msg = "YouTube authentication expired. Please reconnect your YouTube account."
            else:
                error_msg = f"YouTube API error: {e.reason if hasattr(e, 'reason') else 'Upload failed'}"
            print(f"YouTube API error uploading video: {e}")
            return None, error_msg
        except Exception as e:
            error_msg = f"Failed to upload video to YouTube: {str(e)}"
            print(f"Error uploading video: {e}")
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
                    service_type='youtube'
                )
                integration.access_token = self.encrypt_token(credentials.token)
                integration.expires_at = timezone.now() + timedelta(seconds=3600)
                integration.save()
                
                return True
            except Exception as e:
                print(f"Error refreshing YouTube token: {e}")
                return False
        return False