from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from accounts.decorators import role_required
from accounts.models import User
from integrations.youtube import YouTubeService
from integrations.google_drive import GoogleDriveService
from .models import ApprovalRequest
from .forms import ApprovalRequestForm, RejectRequestForm, CreatorDirectUploadForm
import io


@login_required
@role_required(['editor', 'manager', 'creator'])
def create_approval_request(request):
    """View for editors, managers, and creators to create approval requests."""
    if request.method == 'POST':
        form = ApprovalRequestForm(request.user, request.POST)
        if form.is_valid():
            approval_request = form.save(commit=False)
            approval_request.editor = request.user
            approval_request.creator = request.user.get_creator()
            approval_request.status = 'pending'
            approval_request.save()
            
            # Send notification to managers and creator
            notify_managers_and_creator(approval_request)
            
            messages.success(request, f'Approval request for "{approval_request.file.name}" has been submitted successfully.')
            return redirect('approvals:request_list')
    else:
        form = ApprovalRequestForm(request.user)
    
    return render(request, 'approvals/create_request.html', {
        'form': form,
        'title': 'Create Approval Request'
    })


@login_required
@role_required(['editor', 'manager', 'creator'])
def approval_request_list(request):
    """View for editors to see their approval requests."""
    if request.user.is_editor():
        # Editors see only their own requests
        requests = ApprovalRequest.objects.filter(editor=request.user)
        title = 'My Approval Requests'
        is_editor = True
    else:
        # Managers and creators see all requests for their team
        creator = request.user.get_creator()
        requests = ApprovalRequest.objects.filter(creator=creator)
        title = 'All Approval Requests'
        is_editor = False
    
    return render(request, 'approvals/request_list.html', {
        'requests': requests,
        'title': title,
        'is_editor': is_editor
    })


@login_required
@role_required(['manager', 'creator'])
def pending_approvals(request):
    """View for managers and creators to see pending approval requests."""
    creator = request.user.get_creator()
    pending_requests = ApprovalRequest.objects.filter(
        creator=creator,
        status='pending'
    )
    
    return render(request, 'approvals/pending_approvals.html', {
        'requests': pending_requests,
        'title': 'Pending Approvals'
    })


@login_required
@role_required(['editor', 'manager', 'creator'])
def approval_request_detail(request, pk):
    """View for viewing approval request details."""
    approval_request = get_object_or_404(ApprovalRequest, pk=pk)
    
    # Check permissions: editors can only view their own, managers/creators can view all
    if request.user.is_editor() and approval_request.editor != request.user:
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('approvals:request_list')
    
    if request.user.role in ['manager', 'creator']:
        creator = request.user.get_creator()
        if approval_request.creator != creator:
            messages.error(request, 'You do not have permission to view this request.')
            return redirect('approvals:pending_approvals')
    
    return render(request, 'approvals/request_detail.html', {
        'request_obj': approval_request,
        'title': f'Request Details - {approval_request.file.name}',
        'is_editor': request.user.is_editor()
    })


@login_required
@role_required(['manager', 'creator'])
def approve_request(request, pk):
    """View for managers and creators to approve approval requests."""
    approval_request = get_object_or_404(ApprovalRequest, pk=pk)
    
    # Check permissions: only managers/creators from the same team can approve
    creator = request.user.get_creator()
    if approval_request.creator != creator:
        messages.error(request, 'You do not have permission to approve this request.')
        return redirect('approvals:pending_approvals')
    
    # Check if request can be reviewed
    if not approval_request.can_be_reviewed():
        messages.error(request, f'This request has already been {approval_request.status}.')
        return redirect('approvals:request_detail', pk=pk)
    
    # Approve the request
    approval_request.status = 'approved'
    approval_request.reviewed_by = request.user
    approval_request.reviewed_at = timezone.now()
    approval_request.save()
    
    # Send notification to editor
    notify_editor_on_review(approval_request, 'approved')
    
    messages.success(request, f'Approval request for "{approval_request.file.name}" has been approved.')
    return redirect('approvals:request_detail', pk=pk)


@login_required
@role_required(['manager', 'creator'])
def reject_request(request, pk):
    """View for managers and creators to reject approval requests."""
    approval_request = get_object_or_404(ApprovalRequest, pk=pk)
    
    # Check permissions: only managers/creators from the same team can reject
    creator = request.user.get_creator()
    if approval_request.creator != creator:
        messages.error(request, 'You do not have permission to reject this request.')
        return redirect('approvals:pending_approvals')
    
    # Check if request can be reviewed
    if not approval_request.can_be_reviewed():
        messages.error(request, f'This request has already been {approval_request.status}.')
        return redirect('approvals:request_detail', pk=pk)
    
    if request.method == 'POST':
        form = RejectRequestForm(request.POST)
        if form.is_valid():
            # Reject the request
            approval_request.status = 'rejected'
            approval_request.reviewed_by = request.user
            approval_request.reviewed_at = timezone.now()
            approval_request.rejection_reason = form.cleaned_data['rejection_reason']
            approval_request.save()
            
            # Send notification to editor
            notify_editor_on_review(approval_request, 'rejected')
            
            messages.success(request, f'Approval request for "{approval_request.file.name}" has been rejected.')
            return redirect('approvals:request_detail', pk=pk)
    else:
        form = RejectRequestForm()
    
    return render(request, 'approvals/reject_request.html', {
        'form': form,
        'request_obj': approval_request,
        'title': f'Reject Request - {approval_request.file.name}'
    })


@login_required
@role_required(['manager', 'creator'])
def request_history(request):
    """View for managers and creators to see all approval requests with their decisions."""
    creator = request.user.get_creator()
    
    # Get all requests for this team
    all_requests = ApprovalRequest.objects.filter(creator=creator)
    
    # Separate by status for better organization
    pending_requests = all_requests.filter(status='pending')
    approved_requests = all_requests.filter(status='approved')
    rejected_requests = all_requests.filter(status='rejected')
    uploaded_requests = all_requests.filter(status='uploaded')
    
    return render(request, 'approvals/request_history.html', {
        'all_requests': all_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'uploaded_requests': uploaded_requests,
        'title': 'Request History'
    })


def notify_managers_and_creator(approval_request):
    """
    Send notification emails to all managers and the creator about a new approval request.
    
    Args:
        approval_request: The ApprovalRequest instance
    """
    creator = approval_request.creator
    
    # Get all managers and the creator
    recipients = []
    
    # Add creator
    if creator.email:
        recipients.append(creator.email)
    
    # Add all managers in the team
    managers = User.objects.filter(
        creator=creator,
        role='manager'
    )
    for manager in managers:
        if manager.email:
            recipients.append(manager.email)
    
    if not recipients:
        return  # No one to notify
    
    # Prepare email
    subject = f'New Approval Request: {approval_request.file.name}'
    message = f"""
Hello,

{approval_request.editor.username} has submitted a new approval request.

File: {approval_request.file.name}
Description: {approval_request.description or 'No description provided'}
Submitted: {approval_request.created_at.strftime('%Y-%m-%d %H:%M')}

Please review this request in the Creator Backoffice Platform.

Best regards,
Creator Backoffice Platform
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=True,
        )
    except Exception as e:
        # Log the error but don't fail the request creation
        print(f"Failed to send notification email: {e}")


def notify_editor_on_review(approval_request, action):
    """
    Send notification email to the editor about approval/rejection of their request.
    
    Args:
        approval_request: The ApprovalRequest instance
        action: 'approved' or 'rejected'
    """
    editor = approval_request.editor
    
    if not editor.email:
        return  # No email to send to
    
    # Prepare email based on action
    if action == 'approved':
        subject = f'Approval Request Approved: {approval_request.file.name}'
        message = f"""
Hello {editor.username},

Good news! Your approval request has been approved.

File: {approval_request.file.name}
Reviewed by: {approval_request.reviewed_by.username}
Reviewed on: {approval_request.reviewed_at.strftime('%Y-%m-%d %H:%M')}

Your video is now ready to be uploaded to YouTube by a manager or creator.

Best regards,
Creator Backoffice Platform
        """
    else:  # rejected
        subject = f'Approval Request Rejected: {approval_request.file.name}'
        message = f"""
Hello {editor.username},

Your approval request has been rejected.

File: {approval_request.file.name}
Reviewed by: {approval_request.reviewed_by.username}
Reviewed on: {approval_request.reviewed_at.strftime('%Y-%m-%d %H:%M')}

Rejection Reason:
{approval_request.rejection_reason}

Please review the feedback and make necessary changes before resubmitting.

Best regards,
Creator Backoffice Platform
        """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [editor.email],
            fail_silently=True,
        )
    except Exception as e:
        # Log the error but don't fail the review action
        print(f"Failed to send notification email: {e}")


@login_required
@role_required(['manager', 'creator'])
def youtube_upload_list(request):
    """View for managers and creators to see approved videos ready for upload."""
    creator = request.user.get_creator()
    
    # Get all approved requests that haven't been uploaded yet
    approved_requests = ApprovalRequest.objects.filter(
        creator=creator,
        status='approved'
    )
    
    # Check if YouTube is connected
    youtube_service = YouTubeService(user=creator)
    youtube_connected = youtube_service.is_authenticated()
    
    return render(request, 'approvals/youtube_upload_list.html', {
        'requests': approved_requests,
        'title': 'Upload to YouTube',
        'youtube_connected': youtube_connected
    })


@login_required
@role_required(['manager', 'creator'])
def youtube_upload(request, pk):
    """View for managers and creators to upload approved videos to YouTube."""
    approval_request = get_object_or_404(ApprovalRequest, pk=pk)
    
    # Check permissions: only managers/creators from the same team can upload
    creator = request.user.get_creator()
    if approval_request.creator != creator:
        messages.error(request, 'You do not have permission to upload this video.')
        return redirect('approvals:youtube_upload_list')
    
    # Check if request can be uploaded
    if not approval_request.can_be_uploaded():
        messages.error(request, f'This video cannot be uploaded. Current status: {approval_request.status}.')
        return redirect('approvals:youtube_upload_list')
    
    # Check if YouTube is connected
    youtube_service = YouTubeService(user=creator)
    if not youtube_service.is_authenticated():
        messages.error(request, 'YouTube channel is not connected. Please connect your YouTube channel first.')
        return redirect('integrations:dashboard')
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        privacy_status = request.POST.get('privacy_status', 'private')
        tags = request.POST.get('tags', '').strip()
        
        # Validate required fields
        if not title:
            messages.error(request, 'Video title is required.')
            return render(request, 'approvals/youtube_upload.html', {
                'request_obj': approval_request,
                'title': f'Upload to YouTube - {approval_request.file.name}'
            })
        
        if not description:
            messages.error(request, 'Video description is required.')
            return render(request, 'approvals/youtube_upload.html', {
                'request_obj': approval_request,
                'title': f'Upload to YouTube - {approval_request.file.name}'
            })
        
        # Validate privacy status
        valid_privacy = ['private', 'public', 'unlisted']
        if privacy_status not in valid_privacy:
            messages.error(request, 'Invalid privacy status selected.')
            return render(request, 'approvals/youtube_upload.html', {
                'request_obj': approval_request,
                'title': f'Upload to YouTube - {approval_request.file.name}'
            })
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
        
        try:
            # Download file from Google Drive
            drive_service = GoogleDriveService(user=creator)
            drive_api_service, error = drive_service.get_service()
            
            if not drive_api_service:
                messages.error(request, error or 'Google Drive is not connected. Please connect Google Drive first.')
                return redirect('integrations:dashboard')
            
            # Get file from Drive
            from googleapiclient.http import MediaIoBaseDownload
            
            file_id = approval_request.file.file_id
            request_drive = drive_api_service.files().get_media(fileId=file_id)
            
            # Download to memory
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request_drive)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download progress: {int(status.progress() * 100)}%")
            
            # Reset buffer position
            file_buffer.seek(0)
            
            # Upload to YouTube
            result, error_msg = youtube_service.upload_video(
                file_obj=file_buffer,
                title=title,
                description=description,
                privacy_status=privacy_status,
                tags=tag_list
            )
            
            if result:
                # Update approval request status
                approval_request.status = 'uploaded'
                approval_request.youtube_video_id = result['id']
                approval_request.save()
                
                # Notify editor
                notify_editor_on_upload(approval_request, result)
                
                messages.success(
                    request,
                    f'Video "{title}" has been successfully uploaded to YouTube! '
                    f'<a href="{result["url"]}" target="_blank" class="alert-link">View on YouTube</a>'
                )
                return redirect('approvals:youtube_upload_list')
            else:
                messages.error(
                    request,
                    error_msg or 'Failed to upload video to YouTube. Please try again.'
                )
                
        except Exception as e:
            print(f"Error uploading to YouTube: {e}")
            import traceback
            traceback.print_exc()
            messages.error(
                request,
                f'An error occurred while uploading the video: {str(e)}. '
                'Please try again or contact support if the issue persists.'
            )
    
    return render(request, 'approvals/youtube_upload.html', {
        'request_obj': approval_request,
        'title': f'Upload to YouTube - {approval_request.file.name}'
    })


def notify_editor_on_upload(approval_request, upload_result):
    """
    Send notification email to the editor about successful YouTube upload.
    
    Args:
        approval_request: The ApprovalRequest instance
        upload_result: Dict with upload result including video ID and URL
    """
    editor = approval_request.editor
    
    if not editor.email:
        return  # No email to send to
    
    subject = f'Video Uploaded to YouTube: {approval_request.file.name}'
    message = f"""
Hello {editor.username},

Great news! Your video has been successfully uploaded to YouTube.

Video Title: {upload_result.get('title', 'N/A')}
Original File: {approval_request.file.name}
YouTube URL: {upload_result.get('url', 'N/A')}
Privacy Status: {upload_result.get('privacy_status', 'N/A')}
Uploaded: {timezone.now().strftime('%Y-%m-%d %H:%M')}

You can view your video on YouTube using the link above.

Best regards,
Creator Backoffice Platform
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [editor.email],
            fail_silently=True,
        )
    except Exception as e:
        # Log the error but don't fail the upload
        print(f"Failed to send notification email: {e}")


@login_required
@role_required(['creator'])
def creator_direct_upload(request):
    """View for creators to upload videos directly to YouTube without approval."""
    creator = request.user
    
    # Check if YouTube is connected
    youtube_service = YouTubeService(user=creator)
    if not youtube_service.is_authenticated():
        messages.error(request, 'YouTube channel is not connected. Please connect your YouTube channel first.')
        return redirect('integrations:dashboard')
    
    if request.method == 'POST':
        form = CreatorDirectUploadForm(creator, request.POST, request.FILES)
        if form.is_valid():
            source = form.cleaned_data['source']
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            privacy_status = form.cleaned_data['privacy_status']
            tags = form.cleaned_data['tags']
            
            # Parse tags
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
            
            try:
                file_buffer = None
                file_name = None
                
                if source == 'drive':
                    # Download file from Google Drive
                    drive_file = form.cleaned_data['drive_file']
                    file_name = drive_file.name
                    
                    drive_service = GoogleDriveService(user=creator)
                    drive_api_service, error = drive_service.get_service()
                    
                    if not drive_api_service:
                        messages.error(request, error or 'Google Drive is not connected. Please connect Google Drive first.')
                        return redirect('integrations:dashboard')
                    
                    # Get file from Drive
                    from googleapiclient.http import MediaIoBaseDownload
                    
                    file_id = drive_file.file_id
                    request_drive = drive_api_service.files().get_media(fileId=file_id)
                    
                    # Download to memory
                    file_buffer = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_buffer, request_drive)
                    
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            print(f"Download progress: {int(status.progress() * 100)}%")
                    
                    # Reset buffer position
                    file_buffer.seek(0)
                    
                else:  # source == 'upload'
                    # Upload new file to Drive first, then to YouTube
                    uploaded_file = form.cleaned_data['upload_file']
                    file_name = uploaded_file.name
                    
                    # Upload to Drive
                    drive_service = GoogleDriveService(user=creator)
                    drive_api_service, error = drive_service.get_service()
                    
                    if not drive_api_service:
                        messages.error(request, 'Google Drive is not connected. Please connect Google Drive first.')
                        return redirect('integrations:dashboard')
                    
                    from googleapiclient.http import MediaIoBaseUpload
                    
                    # Upload to Drive
                    file_metadata = {
                        'name': uploaded_file.name,
                        'mimeType': uploaded_file.content_type
                    }
                    
                    # Read file content
                    file_content = uploaded_file.read()
                    file_buffer = io.BytesIO(file_content)
                    
                    media = MediaIoBaseUpload(
                        io.BytesIO(file_content),
                        mimetype=uploaded_file.content_type,
                        resumable=True
                    )
                    
                    drive_file_result = drive_api_service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id, name, mimeType, size, modifiedTime, webViewLink'
                    ).execute()
                    
                    # Cache the file in database
                    from files.models import DriveFile
                    from django.utils.dateparse import parse_datetime
                    
                    DriveFile.objects.update_or_create(
                        file_id=drive_file_result['id'],
                        defaults={
                            'name': drive_file_result['name'],
                            'mime_type': drive_file_result['mimeType'],
                            'size': int(drive_file_result.get('size', 0)),
                            'modified_time': parse_datetime(drive_file_result['modifiedTime']),
                            'creator': creator,
                            'web_view_link': drive_file_result.get('webViewLink')
                        }
                    )
                    
                    # Reset buffer for YouTube upload
                    file_buffer.seek(0)
                
                # Upload to YouTube
                result, error_msg = youtube_service.upload_video(
                    file_obj=file_buffer,
                    title=title,
                    description=description,
                    privacy_status=privacy_status,
                    tags=tag_list
                )
                
                if result:
                    messages.success(
                        request,
                        f'Video "{title}" has been successfully uploaded to YouTube! '
                        f'<a href="{result["url"]}" target="_blank" class="alert-link">View on YouTube</a>'
                    )
                    return redirect('approvals:creator_direct_upload')
                else:
                    messages.error(
                        request,
                        error_msg or 'Failed to upload video to YouTube. Please try again.'
                    )
                    
            except Exception as e:
                print(f"Error in creator direct upload: {e}")
                import traceback
                traceback.print_exc()
                messages.error(
                    request,
                    f'An error occurred while uploading the video: {str(e)}. '
                    'Please try again or contact support if the issue persists.'
                )
    else:
        form = CreatorDirectUploadForm(creator)
    
    # Check if Drive is connected
    drive_service = GoogleDriveService(user=creator)
    drive_connected = drive_service.is_authenticated()
    
    return render(request, 'approvals/creator_direct_upload.html', {
        'form': form,
        'title': 'Direct Upload to YouTube',
        'youtube_connected': youtube_service.is_authenticated(),
        'drive_connected': drive_connected
    })
