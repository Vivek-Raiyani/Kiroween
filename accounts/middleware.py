"""
Middleware for permission checking and role-based access control.
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


class PermissionCheckMiddleware:
    """
    Middleware to enforce role-based permissions across the application.
    
    This middleware checks user permissions before processing views and
    ensures that users can only access features appropriate to their role.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define URL patterns and their required roles
        self.role_permissions = {
            # Creator-only URLs
            '/accounts/team/': ['creator'],
            '/accounts/team/add/': ['creator'],
            '/accounts/team/remove/': ['creator'],
            '/integrations/': ['creator'],
            '/integrations/drive/connect/': ['creator'],
            '/integrations/drive/disconnect/': ['creator'],
            '/integrations/youtube/connect/': ['creator'],
            '/integrations/youtube/disconnect/': ['creator'],
            
            # Manager and Creator URLs
            '/approvals/pending/': ['manager', 'creator'],
            '/approvals/review/': ['manager', 'creator'],
            '/integrations/youtube/upload/': ['manager', 'creator'],
            
            # Editor URLs (all authenticated users can access)
            '/approvals/requests/': ['editor', 'manager', 'creator'],
            '/approvals/create/': ['editor', 'manager', 'creator'],
            '/files/': ['editor', 'manager', 'creator'],
            '/files/upload/': ['editor', 'manager', 'creator'],
        }
    
    def __call__(self, request):
        # Skip permission checks for unauthenticated users
        # (login_required decorator will handle this)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Skip permission checks for certain paths
        exempt_paths = [
            '/admin/',
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/register/',  # Both creator and team member registration
            '/static/',
            '/',  # Dashboard
        ]
        
        # Check if path is exempt
        for exempt_path in exempt_paths:
            if request.path.startswith(exempt_path):
                return self.get_response(request)
        
        # Check role permissions for the current path
        for url_pattern, required_roles in self.role_permissions.items():
            if request.path.startswith(url_pattern):
                if request.user.role not in required_roles:
                    messages.error(
                        request,
                        'You do not have permission to access this page. '
                        f'Required role(s): {", ".join(required_roles)}.'
                    )
                    return redirect('permission_denied')
        
        response = self.get_response(request)
        return response


class RoleUpdateMiddleware:
    """
    Middleware to handle immediate permission updates when user roles change.
    
    This middleware ensures that when a user's role is modified, their
    permissions are updated immediately in the current session.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Refresh user from database to get latest role
            # This ensures role changes are reflected immediately
            request.user.refresh_from_db()
        
        response = self.get_response(request)
        return response


class ErrorHandlingMiddleware:
    """
    Middleware to provide consistent error handling and user-friendly error messages.
    
    This middleware catches common exceptions and provides appropriate error messages
    to users while logging detailed information for debugging.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Unhandled exception in request: {request.path}")
            print(f"Error: {e}")
            traceback.print_exc()
            
            # Add user-friendly error message
            if request.user.is_authenticated:
                messages.error(
                    request,
                    'An unexpected error occurred. Please try again or contact support if the problem persists.'
                )
            
            # Re-raise the exception to let Django's error handlers deal with it
            raise
    
    def process_exception(self, request, exception):
        """
        Process exceptions that occur during view execution.
        """
        import traceback
        
        # Log the exception
        print(f"Exception in view: {request.path}")
        print(f"Exception type: {type(exception).__name__}")
        print(f"Exception message: {str(exception)}")
        traceback.print_exc()
        
        # Add user-friendly message for authenticated users
        if request.user.is_authenticated:
            messages.error(
                request,
                'An error occurred while processing your request. '
                'Please try again or contact support if the issue persists.'
            )
        
        # Return None to let Django's default exception handling continue
        return None
