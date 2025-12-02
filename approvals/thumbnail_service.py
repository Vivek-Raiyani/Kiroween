"""
Thumbnail service for handling thumbnail uploads and validation.
"""

import io
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from integrations.youtube import YouTubeService
from integrations.google_drive import GoogleDriveService
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


class ThumbnailService:
    """Service class for thumbnail operations."""
    
    # Thumbnail validation constants
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
    MIN_WIDTH = 1280
    MIN_HEIGHT = 720
    ALLOWED_FORMATS = ['JPEG', 'PNG']
    
    def __init__(self, user=None):
        """Initialize the service with optional user context."""
        self.user = user
    
    def validate_thumbnail(self, file_obj):
        """
        Validate thumbnail file format, size, and dimensions.
        
        Args:
            file_obj: File object or InMemoryUploadedFile
            
        Returns:
            Tuple of (is_valid: bool, error_message: str or None)
        """
        try:
            # Check file size
            if hasattr(file_obj, 'size'):
                if file_obj.size > self.MAX_FILE_SIZE:
                    return False, f"Thumbnail file size must not exceed 2MB. Current size: {file_obj.size / (1024 * 1024):.2f}MB"
            
            # Read image to check format and dimensions
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            try:
                image = Image.open(file_obj)
            except Exception as e:
                return False, f"Invalid image file: {str(e)}"
            
            # Check format
            if image.format not in self.ALLOWED_FORMATS:
                return False, f"Thumbnail must be JPG or PNG format. Current format: {image.format}"
            
            # Check dimensions
            width, height = image.size
            if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                return False, f"Thumbnail dimensions must be at least {self.MIN_WIDTH}x{self.MIN_HEIGHT} pixels. Current: {width}x{height}"
            
            # Reset file pointer
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            return True, None
            
        except Exception as e:
            return False, f"Error validating thumbnail: {str(e)}"
    
    def upload_from_computer(self, file_obj):
        """
        Process thumbnail uploaded from computer.
        
        Args:
            file_obj: Uploaded file object
            
        Returns:
            Tuple of (file_buffer: BytesIO, error_message: str or None)
        """
        try:
            # Validate thumbnail
            is_valid, error_msg = self.validate_thumbnail(file_obj)
            if not is_valid:
                return None, error_msg
            
            # Read file content into buffer
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            file_buffer = io.BytesIO(file_obj.read())
            file_buffer.seek(0)
            
            return file_buffer, None
            
        except Exception as e:
            return None, f"Error processing thumbnail upload: {str(e)}"
    
    def get_from_drive(self, file_id):
        """
        Download thumbnail from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Tuple of (file_buffer: BytesIO, error_message: str or None)
        """
        if not self.user:
            return None, "No user specified"
        
        try:
            # Get Drive service
            drive_service = GoogleDriveService(user=self.user)
            service, error = drive_service.get_service()
            
            if not service:
                return None, error or "Google Drive is not connected"
            
            # Download file from Drive
            request = service.files().get_media(fileId=file_id)
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            # Reset buffer position
            file_buffer.seek(0)
            
            # Validate the downloaded thumbnail
            is_valid, error_msg = self.validate_thumbnail(file_buffer)
            if not is_valid:
                return None, error_msg
            
            return file_buffer, None
            
        except Exception as e:
            return None, f"Error downloading thumbnail from Google Drive: {str(e)}"
    
    def extract_frame(self, video_file_obj, timestamp):
        """
        Extract a frame from video at specified timestamp.
        
        Args:
            video_file_obj: Video file object or BytesIO
            timestamp: Time in seconds to extract frame
            
        Returns:
            Tuple of (file_buffer: BytesIO, error_message: str or None)
        """
        try:
            # Note: Frame extraction requires ffmpeg or similar video processing library
            # For now, we'll return an error indicating this feature needs additional setup
            return None, (
                "Frame extraction from video requires ffmpeg installation. "
                "Please upload a custom thumbnail or select from Google Drive instead."
            )
            
            # TODO: Implement frame extraction using ffmpeg-python or similar
            # Example implementation would be:
            # 1. Save video to temp file
            # 2. Use ffmpeg to extract frame at timestamp
            # 3. Load extracted frame as image
            # 4. Validate dimensions
            # 5. Return as BytesIO buffer
            
        except Exception as e:
            return None, f"Error extracting frame from video: {str(e)}"
    
    def set_youtube_thumbnail(self, video_id, thumbnail_buffer):
        """
        Upload thumbnail to YouTube for a specific video.
        
        Args:
            video_id: YouTube video ID
            thumbnail_buffer: BytesIO buffer containing thumbnail image
            
        Returns:
            Tuple of (success: bool, error_message: str or None)
        """
        if not self.user:
            return False, "No user specified"
        
        try:
            # Get YouTube service
            youtube_service = YouTubeService(user=self.user)
            service, error = youtube_service.get_service()
            
            if not service:
                return False, error or "YouTube is not connected"
            
            # Validate thumbnail before upload
            is_valid, error_msg = self.validate_thumbnail(thumbnail_buffer)
            if not is_valid:
                return False, error_msg
            
            # Create media upload object
            media = MediaIoBaseUpload(
                thumbnail_buffer,
                mimetype='image/jpeg',
                resumable=True
            )
            
            # Upload thumbnail to YouTube
            request = service.thumbnails().set(
                videoId=video_id,
                media_body=media
            )
            
            response = request.execute()
            
            if response:
                return True, None
            else:
                return False, "Failed to set thumbnail on YouTube"
            
        except Exception as e:
            error_msg = f"Error uploading thumbnail to YouTube: {str(e)}"
            print(f"Thumbnail upload error: {e}")
            import traceback
            traceback.print_exc()
            return False, error_msg
