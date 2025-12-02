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
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube.readonly',  # For Analytics API
        'https://www.googleapis.com/auth/youtube.force-ssl'  # For metadata updates (A/B testing)
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
                    'scopes': ' '.join(granted_scopes),  # Store granted scopes
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


class YouTubeAnalyticsService:
    """Service class for YouTube Analytics API operations."""
    
    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1  # seconds
    MAX_BACKOFF = 16  # seconds
    
    def __init__(self, user=None):
        """Initialize the analytics service with optional user context."""
        self.user = user
        self._youtube_service = None
        self._analytics_service = None
        self._credentials = None
    
    def _execute_with_retry(self, request, operation_name="API call"):
        """
        Execute an API request with exponential backoff retry logic.
        
        Args:
            request: The API request object to execute
            operation_name: Description of the operation for logging
            
        Returns:
            Tuple of (response, error_message)
        """
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        backoff = self.INITIAL_BACKOFF
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = request.execute()
                return response, None
                
            except HttpError as e:
                error_code = e.resp.status
                
                # Handle rate limiting (429) and server errors (5xx)
                if error_code == 429 or (500 <= error_code < 600):
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = min(backoff, self.MAX_BACKOFF)
                        logger.warning(
                            f"{operation_name} failed with error {error_code}. "
                            f"Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        time.sleep(wait_time)
                        backoff *= 2  # Exponential backoff
                        continue
                    else:
                        error_msg = f"Rate limit exceeded or server error after {self.MAX_RETRIES} attempts"
                        logger.error(f"{operation_name} failed: {error_msg}")
                        return None, error_msg
                
                # Handle authentication errors (401)
                elif error_code == 401:
                    # Try to refresh token automatically
                    logger.info(f"Authentication error during {operation_name}. Attempting token refresh...")
                    credentials, cred_error = self.get_credentials()
                    if credentials:
                        # Token was refreshed, retry once
                        if attempt < self.MAX_RETRIES - 1:
                            logger.info("Token refreshed successfully. Retrying request...")
                            # Rebuild services with new credentials
                            self._youtube_service = None
                            self._analytics_service = None
                            continue
                    
                    error_msg = "Authentication failed. Please reconnect your YouTube account."
                    logger.error(f"{operation_name} failed: {error_msg}")
                    return None, error_msg
                
                # Handle quota exceeded (403)
                elif error_code == 403:
                    error_msg = "YouTube API quota exceeded. Please try again later."
                    logger.error(f"{operation_name} failed: {error_msg}")
                    return None, error_msg
                
                # Other HTTP errors
                else:
                    error_msg = f"YouTube API error: {e.reason if hasattr(e, 'reason') else str(e)}"
                    logger.error(f"{operation_name} failed: {error_msg}")
                    return None, error_msg
                    
            except Exception as e:
                error_msg = f"Unexpected error during {operation_name}: {str(e)}"
                logger.error(error_msg)
                return None, error_msg
        
        # Should not reach here, but just in case
        return None, f"{operation_name} failed after {self.MAX_RETRIES} attempts"
    
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
            youtube_service = YouTubeService(user=self.user)
            access_token = youtube_service.decrypt_token(integration.access_token)
            refresh_token = youtube_service.decrypt_token(integration.refresh_token) if integration.refresh_token else None
            
            # Create credentials object
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.YOUTUBE_CLIENT_ID,
                client_secret=settings.YOUTUBE_CLIENT_SECRET,
                scopes=YouTubeService.SCOPES
            )
            
            # Check if token needs refresh
            if integration.is_expired():
                try:
                    credentials.refresh(Request())
                    
                    # Update stored tokens
                    integration.access_token = youtube_service.encrypt_token(credentials.token)
                    integration.expires_at = timezone.now() + timedelta(seconds=3600)
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
    
    def get_youtube_service(self):
        """
        Get authenticated YouTube Data API service.
        Returns tuple (service, error_message)
        """
        if self._youtube_service:
            return self._youtube_service, None
        
        credentials, error = self.get_credentials()
        if not credentials:
            return None, error or "Could not get YouTube credentials"
        
        try:
            self._youtube_service = build('youtube', 'v3', credentials=credentials)
            return self._youtube_service, None
        except Exception as e:
            print(f"Error building YouTube service: {e}")
            return None, f"Could not connect to YouTube: {str(e)}"
    
    def get_analytics_service(self):
        """
        Get authenticated YouTube Analytics API service.
        Returns tuple (service, error_message)
        """
        if self._analytics_service:
            return self._analytics_service, None
        
        credentials, error = self.get_credentials()
        if not credentials:
            return None, error or "Could not get YouTube credentials"
        
        try:
            self._analytics_service = build('youtubeAnalytics', 'v2', credentials=credentials)
            return self._analytics_service, None
        except Exception as e:
            print(f"Error building YouTube Analytics service: {e}")
            return None, f"Could not connect to YouTube Analytics: {str(e)}"
    
    def get_channel_id(self):
        """
        Get the channel ID for the authenticated user.
        Returns tuple (channel_id, error_message)
        """
        youtube_service, error = self.get_youtube_service()
        if not youtube_service:
            return None, error
        
        try:
            request = youtube_service.channels().list(
                part='id',
                mine=True
            )
            response = request.execute()
            
            if response.get('items'):
                return response['items'][0]['id'], None
            
            return None, "No channel found for this account"
            
        except HttpError as e:
            error_msg = f"YouTube API error: {e.reason if hasattr(e, 'reason') else str(e)}"
            print(f"YouTube API error getting channel ID: {e}")
            return None, error_msg
        except Exception as e:
            error_msg = f"Error getting channel ID: {str(e)}"
            print(f"Error getting channel ID: {e}")
            return None, error_msg
    
    def get_video_metrics(self, video_id, start_date, end_date):
        """
        Fetch video analytics metrics for a specific video.
        
        Args:
            video_id: YouTube video ID
            start_date: Start date (YYYY-MM-DD format or datetime object)
            end_date: End date (YYYY-MM-DD format or datetime object)
            
        Returns:
            Tuple of (metrics dict, error_message)
        """
        analytics_service, error = self.get_analytics_service()
        if not analytics_service:
            return None, error
        
        # Convert datetime objects to string format if needed
        if hasattr(start_date, 'strftime'):
            start_date = start_date.strftime('%Y-%m-%d')
        if hasattr(end_date, 'strftime'):
            end_date = end_date.strftime('%Y-%m-%d')
        
        # Fetch video metrics with retry logic
        request = analytics_service.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='views,likes,comments,shares,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost',
            dimensions='day',
            filters=f'video=={video_id}',
            sort='day'
        )
        
        response, error = self._execute_with_retry(request, f"get_video_metrics for {video_id}")
        if error:
            return None, error
        
        # Parse response
        metrics = {
            'video_id': video_id,
            'start_date': start_date,
            'end_date': end_date,
            'rows': []
        }
        
        if 'rows' in response:
            column_headers = [header['name'] for header in response.get('columnHeaders', [])]
            for row in response['rows']:
                row_data = dict(zip(column_headers, row))
                metrics['rows'].append(row_data)
        
        return metrics, None
    
    def get_channel_metrics(self, start_date, end_date):
        """
        Fetch channel-level analytics metrics.
        
        Args:
            start_date: Start date (YYYY-MM-DD format or datetime object)
            end_date: End date (YYYY-MM-DD format or datetime object)
            
        Returns:
            Tuple of (metrics dict, error_message)
        """
        analytics_service, error = self.get_analytics_service()
        if not analytics_service:
            return None, error
        
        # Convert datetime objects to string format if needed
        if hasattr(start_date, 'strftime'):
            start_date = start_date.strftime('%Y-%m-%d')
        if hasattr(end_date, 'strftime'):
            end_date = end_date.strftime('%Y-%m-%d')
        
        # Fetch channel metrics with retry logic
        request = analytics_service.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='views,likes,comments,shares,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost',
            dimensions='day',
            sort='day'
        )
        
        response, error = self._execute_with_retry(request, "get_channel_metrics")
        if error:
            return None, error
        
        # Parse response
        metrics = {
            'start_date': start_date,
            'end_date': end_date,
            'rows': []
        }
        
        if 'rows' in response:
            column_headers = [header['name'] for header in response.get('columnHeaders', [])]
            for row in response['rows']:
                row_data = dict(zip(column_headers, row))
                metrics['rows'].append(row_data)
        
        return metrics, None
    
    def get_traffic_sources(self, video_id, start_date, end_date):
        """
        Fetch traffic source data for a video.
        
        Args:
            video_id: YouTube video ID
            start_date: Start date (YYYY-MM-DD format or datetime object)
            end_date: End date (YYYY-MM-DD format or datetime object)
            
        Returns:
            Tuple of (traffic sources dict, error_message)
        """
        analytics_service, error = self.get_analytics_service()
        if not analytics_service:
            return None, error
        
        # Convert datetime objects to string format if needed
        if hasattr(start_date, 'strftime'):
            start_date = start_date.strftime('%Y-%m-%d')
        if hasattr(end_date, 'strftime'):
            end_date = end_date.strftime('%Y-%m-%d')
        
        # Fetch traffic source data with retry logic
        request = analytics_service.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='views,estimatedMinutesWatched',
            dimensions='insightTrafficSourceType',
            filters=f'video=={video_id}',
            sort='-views'
        )
        
        response, error = self._execute_with_retry(request, f"get_traffic_sources for {video_id}")
        if error:
            return None, error
        
        # Parse response
        traffic_sources = {
            'video_id': video_id,
            'start_date': start_date,
            'end_date': end_date,
            'sources': []
        }
        
        if 'rows' in response:
            column_headers = [header['name'] for header in response.get('columnHeaders', [])]
            for row in response['rows']:
                row_data = dict(zip(column_headers, row))
                traffic_sources['sources'].append(row_data)
        
        return traffic_sources, None
    
    def get_demographics(self, video_id, start_date, end_date):
        """
        Fetch demographic data (age and gender) for a video.
        
        Args:
            video_id: YouTube video ID
            start_date: Start date (YYYY-MM-DD format or datetime object)
            end_date: End date (YYYY-MM-DD format or datetime object)
            
        Returns:
            Tuple of (demographics dict, error_message)
        """
        analytics_service, error = self.get_analytics_service()
        if not analytics_service:
            return None, error
        
        # Convert datetime objects to string format if needed
        if hasattr(start_date, 'strftime'):
            start_date = start_date.strftime('%Y-%m-%d')
        if hasattr(end_date, 'strftime'):
            end_date = end_date.strftime('%Y-%m-%d')
        
        demographics = {
            'video_id': video_id,
            'start_date': start_date,
            'end_date': end_date,
            'age_gender': [],
            'geography': []
        }
        
        # Fetch age and gender demographics with retry logic
        request = analytics_service.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='viewerPercentage',
            dimensions='ageGroup,gender',
            filters=f'video=={video_id}',
            sort='-viewerPercentage'
        )
        
        response, error = self._execute_with_retry(request, f"get_demographics (age/gender) for {video_id}")
        if not error and response and 'rows' in response:
            column_headers = [header['name'] for header in response.get('columnHeaders', [])]
            for row in response['rows']:
                row_data = dict(zip(column_headers, row))
                demographics['age_gender'].append(row_data)
        
        # Fetch geographic demographics with retry logic
        request = analytics_service.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='views,estimatedMinutesWatched',
            dimensions='country',
            filters=f'video=={video_id}',
            sort='-views',
            maxResults=10
        )
        
        response, error = self._execute_with_retry(request, f"get_demographics (geography) for {video_id}")
        if not error and response and 'rows' in response:
            column_headers = [header['name'] for header in response.get('columnHeaders', [])]
            for row in response['rows']:
                row_data = dict(zip(column_headers, row))
                demographics['geography'].append(row_data)
        
        return demographics, None
    
    def get_retention_data(self, video_id):
        """
        Fetch audience retention data for a video.
        
        Note: Audience retention data is available through the YouTube Data API,
        not the Analytics API. This method uses the videos.getReport endpoint.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Tuple of (retention data dict, error_message)
        """
        youtube_service, error = self.get_youtube_service()
        if not youtube_service:
            return None, error
        
        # Note: Detailed retention curves require YouTube Studio API access
        # which is not available in the standard YouTube Data API v3.
        # We'll return basic video statistics instead and note this limitation.
        
        request = youtube_service.videos().list(
            part='statistics,contentDetails',
            id=video_id
        )
        
        response, error = self._execute_with_retry(request, f"get_retention_data for {video_id}")
        if error:
            return None, error
        
        if not response.get('items'):
            return None, f"Video {video_id} not found"
        
        video = response['items'][0]
        
        # Calculate approximate retention metrics from available data
        retention_data = {
            'video_id': video_id,
            'view_count': int(video['statistics'].get('viewCount', 0)),
            'like_count': int(video['statistics'].get('likeCount', 0)),
            'comment_count': int(video['statistics'].get('commentCount', 0)),
            'duration': video['contentDetails'].get('duration', 'PT0S'),
            'note': 'Detailed retention curve requires YouTube Studio API access. Using basic statistics.'
        }
        
        return retention_data, None