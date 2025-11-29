from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime
from accounts.decorators import role_required
from integrations.google_drive import GoogleDriveService
from .models import DriveFile


@login_required
@role_required(['editor', 'manager', 'creator'])
def file_list(request):
    """Display list of files from Google Drive with search and pagination."""
    user = request.user
    creator = user.get_creator()
    
    # Check if Drive is connected
    drive_service = GoogleDriveService(user=creator)
    if not drive_service.is_authenticated():
        messages.warning(request, 'Google Drive is not connected. Please connect your Google Drive account.')
        return render(request, 'files/file_list.html', {
            'files': [],
            'drive_connected': False,
            'search_query': '',
        })
    
    # Get search query
    search_query = request.GET.get('q', '').strip()
    
    # Sync files from Google Drive
    success, error = sync_files_from_drive(creator, search_query)
    if not success and error:
        messages.warning(request, f'Could not sync files from Google Drive: {error}')
    
    # Get files from database
    files_queryset = DriveFile.objects.filter(creator=creator)
    
    if search_query:
        files_queryset = files_queryset.filter(name__icontains=search_query)
    
    # Pagination
    paginator = Paginator(files_queryset, 20)  # 20 files per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'files/file_list.html', {
        'page_obj': page_obj,
        'files': page_obj.object_list,
        'drive_connected': True,
        'search_query': search_query,
    })


@login_required
@role_required(['editor', 'manager', 'creator'])
def file_detail(request, file_id):
    """Display file details with preview/download options."""
    user = request.user
    creator = user.get_creator()
    
    # Get file from database
    file = get_object_or_404(DriveFile, file_id=file_id, creator=creator)
    
    # Check if Drive is connected
    drive_service = GoogleDriveService(user=creator)
    if not drive_service.is_authenticated():
        messages.error(request, 'Google Drive is not connected.')
        return redirect('files:file_list')
    
    # Get fresh file metadata from Drive
    drive_file = drive_service.get_file(file_id)
    if drive_file:
        # Update cached metadata
        file.name = drive_file.get('name', file.name)
        file.mime_type = drive_file.get('mimeType', file.mime_type)
        file.size = int(drive_file.get('size', 0)) if drive_file.get('size') else None
        file.web_view_link = drive_file.get('webViewLink', file.web_view_link)
        
        # Parse modified time
        if drive_file.get('modifiedTime'):
            try:
                modified_time = datetime.fromisoformat(drive_file['modifiedTime'].replace('Z', '+00:00'))
                file.modified_time = modified_time
            except:
                pass
        
        file.save()
    
    return render(request, 'files/file_detail.html', {
        'file': file,
        'can_delete': user.is_creator(),
    })


@login_required
@role_required(['editor', 'manager', 'creator'])
def file_upload(request):
    """Handle file upload to Google Drive."""
    user = request.user
    creator = user.get_creator()
    
    # Check if Drive is connected
    drive_service = GoogleDriveService(user=creator)
    if not drive_service.is_authenticated():
        messages.error(request, 'Google Drive is not connected. Please connect your Google Drive account.')
        return redirect('files:file_list')
    
    # Get quota information for display
    quota_info = None
    if request.method == 'GET':
        quota = drive_service.get_storage_quota()
        if quota:
            quota_info = {
                'limit_gb': quota['limit'] / (1024**3) if quota['limit'] > 0 else 0,
                'usage_gb': quota['usage'] / (1024**3),
                'available_gb': quota['available'] / (1024**3) if quota['available'] != float('inf') else 0,
                'usage_percent': (quota['usage'] / quota['limit'] * 100) if quota['limit'] > 0 else 0,
            }
    
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        
        if not uploaded_file:
            messages.error(request, 'Please select a file to upload.')
            return redirect('files:file_upload')
        
        # Validate file size against Drive quota
        is_valid, validation_message = drive_service.validate_file_size(uploaded_file.size)
        
        if not is_valid:
            messages.error(request, validation_message)
            return redirect('files:file_upload')
        
        # Additional safety check: 5GB per file limit (Google Drive limit)
        max_single_file_size = 5 * 1024 * 1024 * 1024  # 5GB
        if uploaded_file.size > max_single_file_size:
            messages.error(request, f'File size exceeds the maximum single file limit of 5GB.')
            return redirect('files:file_upload')
        
        try:
            # Upload to Google Drive
            result, error_msg = drive_service.upload_file(
                file_obj=uploaded_file,
                filename=uploaded_file.name,
                mime_type=uploaded_file.content_type
            )
            
            if result:
                # Cache the file metadata
                modified_time = datetime.fromisoformat(result['modifiedTime'].replace('Z', '+00:00'))
                
                DriveFile.objects.update_or_create(
                    file_id=result['id'],
                    defaults={
                        'name': result['name'],
                        'mime_type': result['mimeType'],
                        'size': int(result.get('size', 0)) if result.get('size') else None,
                        'modified_time': modified_time,
                        'creator': creator,
                        'web_view_link': result.get('webViewLink'),
                    }
                )
                
                messages.success(request, f'File "{uploaded_file.name}" uploaded successfully to Google Drive!')
                return redirect('files:file_list')
            else:
                messages.error(request, error_msg or 'Failed to upload file to Google Drive. Please try again.')
                
        except Exception as e:
            messages.error(request, f'An unexpected error occurred while uploading: {str(e)}. Please try again.')
            print(f"Unexpected error in file upload: {e}")
            import traceback
            traceback.print_exc()
            return redirect('files:file_upload')
    
    return render(request, 'files/file_upload.html', {
        'quota_info': quota_info,
    })


@login_required
@role_required(['creator'])
def file_delete(request, file_id):
    """Delete a file (creator only)."""
    user = request.user
    creator = user.get_creator()
    
    file = get_object_or_404(DriveFile, file_id=file_id, creator=creator)
    
    if request.method == 'POST':
        file_name = file.name
        file.delete()
        messages.success(request, f'File "{file_name}" removed from cache.')
        return redirect('files:file_list')
    
    return render(request, 'files/file_delete_confirm.html', {'file': file})


def sync_files_from_drive(creator, search_query=None):
    """
    Sync file metadata from Google Drive to local database.
    
    Args:
        creator: The creator user whose Drive to sync
        search_query: Optional search query to filter files
        
    Returns:
        Tuple of (success: bool, error_message: str or None)
    """
    drive_service = GoogleDriveService(user=creator)
    
    if not drive_service.is_authenticated():
        return False, "Google Drive is not connected"
    
    try:
        # Get files from Drive
        result, error = drive_service.list_files(query=search_query, page_size=100)
        
        if error:
            return False, error
        
        drive_files = result.get('files', [])
        
        # Update or create cached files
        synced_count = 0
        for drive_file in drive_files:
            try:
                # Parse modified time
                modified_time = datetime.fromisoformat(drive_file['modifiedTime'].replace('Z', '+00:00'))
                
                DriveFile.objects.update_or_create(
                    file_id=drive_file['id'],
                    defaults={
                        'name': drive_file['name'],
                        'mime_type': drive_file['mimeType'],
                        'size': int(drive_file.get('size', 0)) if drive_file.get('size') else None,
                        'modified_time': modified_time,
                        'creator': creator,
                        'web_view_link': drive_file.get('webViewLink'),
                    }
                )
                synced_count += 1
            except Exception as e:
                print(f"Error syncing file {drive_file.get('id')}: {e}")
                continue
        
        return True, None
                
    except Exception as e:
        error_msg = f"Error syncing files from Drive: {str(e)}"
        print(error_msg)
        return False, error_msg
