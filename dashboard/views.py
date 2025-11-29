from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from approvals.models import ApprovalRequest
from files.models import DriveFile
from integrations.models import Integration


@login_required
def dashboard_view(request):
    """Display role-appropriate dashboard."""
    user = request.user
    creator = user.get_creator()
    
    context = {
        'user': user,
        'role': user.role,
    }
    
    # Add role-specific data
    if user.is_editor():
        context.update(_get_editor_dashboard_data(user, creator))
    elif user.is_manager():
        context.update(_get_manager_dashboard_data(user, creator))
    elif user.is_creator():
        context.update(_get_creator_dashboard_data(user))
    
    return render(request, 'dashboard/dashboard.html', context)


def _get_editor_dashboard_data(user, creator):
    """Get dashboard data for editors."""
    # Recent files (last 5)
    recent_files = DriveFile.objects.filter(
        creator=creator
    ).order_by('-modified_time')[:5]
    
    # Pending requests by this editor
    pending_requests = ApprovalRequest.objects.filter(
        editor=user,
        status='pending'
    ).select_related('file')
    
    # Upload statistics
    total_requests = ApprovalRequest.objects.filter(editor=user).count()
    approved_requests = ApprovalRequest.objects.filter(
        editor=user,
        status='approved'
    ).count()
    rejected_requests = ApprovalRequest.objects.filter(
        editor=user,
        status='rejected'
    ).count()
    uploaded_requests = ApprovalRequest.objects.filter(
        editor=user,
        status='uploaded'
    ).count()
    
    # Recent requests (last 5)
    recent_requests = ApprovalRequest.objects.filter(
        editor=user
    ).select_related('file', 'reviewed_by').order_by('-created_at')[:5]
    
    return {
        'recent_files': recent_files,
        'pending_requests': pending_requests,
        'pending_requests_count': pending_requests.count(),
        'total_requests': total_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'uploaded_requests': uploaded_requests,
        'recent_requests': recent_requests,
    }


def _get_manager_dashboard_data(user, creator):
    """Get dashboard data for managers."""
    # Pending approvals for this creator's team
    pending_approvals = ApprovalRequest.objects.filter(
        creator=creator,
        status='pending'
    ).select_related('editor', 'file').order_by('-created_at')
    
    # Recent uploads (videos that have been uploaded to YouTube)
    recent_uploads = ApprovalRequest.objects.filter(
        creator=creator,
        status='uploaded'
    ).select_related('editor', 'file', 'reviewed_by').order_by('-reviewed_at')[:5]
    
    # Team activity - recent approval requests
    team_activity = ApprovalRequest.objects.filter(
        creator=creator
    ).select_related('editor', 'file', 'reviewed_by').order_by('-created_at')[:10]
    
    # Statistics
    total_pending = pending_approvals.count()
    total_approved = ApprovalRequest.objects.filter(
        creator=creator,
        status='approved'
    ).count()
    total_uploaded = ApprovalRequest.objects.filter(
        creator=creator,
        status='uploaded'
    ).count()
    
    # Requests reviewed by this manager
    reviewed_by_me = ApprovalRequest.objects.filter(
        reviewed_by=user
    ).count()
    
    return {
        'pending_approvals': pending_approvals,
        'pending_approvals_count': total_pending,
        'recent_uploads': recent_uploads,
        'team_activity': team_activity,
        'total_approved': total_approved,
        'total_uploaded': total_uploaded,
        'reviewed_by_me': reviewed_by_me,
    }


def _get_creator_dashboard_data(user):
    """Get dashboard data for creators."""
    # Team overview
    team_members = User.objects.filter(creator=user).select_related('creator')
    total_members = team_members.count()
    managers_count = team_members.filter(role='manager').count()
    editors_count = team_members.filter(role='editor').count()
    
    # Integration status
    integrations = Integration.objects.filter(user=user)
    drive_connected = integrations.filter(service_type='google_drive').exists()
    youtube_connected = integrations.filter(service_type='youtube').exists()
    
    # Platform statistics
    total_files = DriveFile.objects.filter(creator=user).count()
    total_requests = ApprovalRequest.objects.filter(creator=user).count()
    pending_requests = ApprovalRequest.objects.filter(
        creator=user,
        status='pending'
    ).count()
    approved_requests = ApprovalRequest.objects.filter(
        creator=user,
        status='approved'
    ).count()
    uploaded_videos = ApprovalRequest.objects.filter(
        creator=user,
        status='uploaded'
    ).count()
    
    # Recent activity
    recent_requests = ApprovalRequest.objects.filter(
        creator=user
    ).select_related('editor', 'file', 'reviewed_by').order_by('-created_at')[:10]
    
    # Recent files
    recent_files = DriveFile.objects.filter(
        creator=user
    ).order_by('-modified_time')[:5]
    
    # Activity in last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_activity_count = ApprovalRequest.objects.filter(
        creator=user,
        created_at__gte=seven_days_ago
    ).count()
    
    return {
        'team_members': team_members,
        'total_members': total_members,
        'managers_count': managers_count,
        'editors_count': editors_count,
        'drive_connected': drive_connected,
        'youtube_connected': youtube_connected,
        'total_files': total_files,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'uploaded_videos': uploaded_videos,
        'recent_requests': recent_requests,
        'recent_files': recent_files,
        'recent_activity_count': recent_activity_count,
    }
