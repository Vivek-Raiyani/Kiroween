from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from accounts.decorators import role_required
from .google_drive import GoogleDriveService
from .youtube import YouTubeService
from .models import Integration


@login_required
@role_required(['creator'])
def integrations_dashboard(request):
    """Main integrations dashboard for creators."""
    # Check current integrations
    drive_integration = Integration.objects.filter(
        user=request.user,
        service_type='google_drive'
    ).first()
    
    youtube_integration = Integration.objects.filter(
        user=request.user,
        service_type='youtube'
    ).first()
    
    context = {
        'drive_connected': drive_integration is not None,
        'youtube_connected': youtube_integration is not None,
        'drive_integration': drive_integration,
        'youtube_integration': youtube_integration,
    }
    
    return render(request, 'integrations/dashboard.html', context)


@login_required
@role_required(['creator'])
def google_drive_connect(request):
    """Initiate Google Drive OAuth flow."""
    try:
        drive_service = GoogleDriveService(user=request.user)
        
        # Build redirect URI
        redirect_uri = request.build_absolute_uri(reverse('integrations:google_drive_callback'))
        
        # Get authorization URL
        auth_url = drive_service.get_authorization_url(redirect_uri)
        
        return redirect(auth_url)
        
    except Exception as e:
        messages.error(request, f'Error initiating Google Drive connection: {str(e)}')
        return redirect('integrations:dashboard')


@login_required
@role_required(['creator'])
def google_drive_callback(request):
    """Handle Google Drive OAuth callback."""
    authorization_code = request.GET.get('code')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description', '')
    
    if error:
        if error == 'access_denied':
            messages.warning(request, 'Google Drive connection was cancelled. You can try again when ready.')
        else:
            error_msg = error_description if error_description else error
            messages.error(request, f'Google Drive authorization failed: {error_msg}')
        return redirect('integrations:dashboard')
    
    if not authorization_code:
        messages.error(request, 'No authorization code received from Google. Please try connecting again.')
        return redirect('integrations:dashboard')
    
    try:
        drive_service = GoogleDriveService(user=request.user)
        redirect_uri = request.build_absolute_uri(reverse('integrations:google_drive_callback'))
        
        # Exchange code for tokens
        success, error_msg = drive_service.authenticate(authorization_code, redirect_uri)
        
        if success:
            messages.success(request, 'Google Drive connected successfully! You can now access your files.')
        else:
            messages.error(request, error_msg or 'Failed to connect Google Drive. Please try again.')
            
    except Exception as e:
        messages.error(request, f'An unexpected error occurred while connecting Google Drive. Please try again or contact support.')
        print(f"Unexpected error in Drive callback: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect('integrations:dashboard')


@login_required
@role_required(['creator'])
@require_http_methods(["POST"])
def google_drive_disconnect(request):
    """Disconnect Google Drive integration."""
    try:
        drive_service = GoogleDriveService(user=request.user)
        success = drive_service.disconnect()
        
        if success:
            messages.success(request, 'Google Drive disconnected successfully.')
        else:
            messages.error(request, 'Failed to disconnect Google Drive.')
            
    except Exception as e:
        messages.error(request, f'Error disconnecting Google Drive: {str(e)}')
    
    return redirect('integrations:dashboard')


@login_required
@role_required(['creator'])
def google_drive_status(request):
    """Check Google Drive connection status (AJAX endpoint)."""
    try:
        drive_service = GoogleDriveService(user=request.user)
        is_connected = drive_service.is_authenticated()
        
        return JsonResponse({
            'connected': is_connected,
            'status': 'connected' if is_connected else 'disconnected'
        })
        
    except Exception as e:
        return JsonResponse({
            'connected': False,
            'status': 'error',
            'error': str(e)
        })


@login_required
@role_required(['creator'])
def youtube_connect(request):
    """Initiate YouTube OAuth flow."""
    try:
        youtube_service = YouTubeService(user=request.user)
        
        # Build redirect URI
        redirect_uri = request.build_absolute_uri(reverse('integrations:youtube_callback'))
        
        # Get authorization URL
        auth_url = youtube_service.get_authorization_url(redirect_uri)
        
        return redirect(auth_url)
        
    except Exception as e:
        messages.error(request, f'Error initiating YouTube connection: {str(e)}')
        return redirect('integrations:dashboard')


@login_required
@role_required(['creator'])
def youtube_callback(request):
    """Handle YouTube OAuth callback."""
    authorization_code = request.GET.get('code')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description', '')
    
    if error:
        if error == 'access_denied':
            messages.warning(request, 'YouTube connection was cancelled. You can try again when ready.')
        else:
            error_msg = error_description if error_description else error
            messages.error(request, f'YouTube authorization failed: {error_msg}')
        return redirect('integrations:dashboard')
    
    if not authorization_code:
        messages.error(request, 'No authorization code received from Google. Please try connecting again.')
        return redirect('integrations:dashboard')
    
    try:
        youtube_service = YouTubeService(user=request.user)
        redirect_uri = request.build_absolute_uri(reverse('integrations:youtube_callback'))
        
        # Exchange code for tokens
        success, error_msg = youtube_service.authenticate(authorization_code, redirect_uri)
        
        if success:
            messages.success(request, 'YouTube channel connected successfully! You can now upload videos.')
        else:
            messages.error(request, error_msg or 'Failed to connect YouTube channel. Please try again.')
            
    except Exception as e:
        messages.error(request, f'An unexpected error occurred while connecting YouTube. Please try again or contact support.')
        print(f"Unexpected error in YouTube callback: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect('integrations:dashboard')


@login_required
@role_required(['creator'])
@require_http_methods(["POST"])
def youtube_disconnect(request):
    """Disconnect YouTube integration."""
    try:
        youtube_service = YouTubeService(user=request.user)
        success = youtube_service.disconnect()
        
        if success:
            messages.success(request, 'YouTube channel disconnected successfully.')
        else:
            messages.error(request, 'Failed to disconnect YouTube channel.')
            
    except Exception as e:
        messages.error(request, f'Error disconnecting YouTube: {str(e)}')
    
    return redirect('integrations:dashboard')


@login_required
@role_required(['creator'])
def youtube_status(request):
    """Check YouTube connection status (AJAX endpoint)."""
    try:
        youtube_service = YouTubeService(user=request.user)
        is_connected = youtube_service.is_authenticated()
        
        channel_info = None
        error_msg = None
        if is_connected:
            channel_info, error_msg = youtube_service.get_channel_info()
        
        return JsonResponse({
            'connected': is_connected,
            'status': 'connected' if is_connected else 'disconnected',
            'channel_info': channel_info,
            'error': error_msg
        })
        
    except Exception as e:
        return JsonResponse({
            'connected': False,
            'status': 'error',
            'error': str(e)
        })


@login_required
def placeholder_team(request):
    """Placeholder view for team management."""
    return render(request, 'placeholder.html', {'feature': 'Team Management'})
