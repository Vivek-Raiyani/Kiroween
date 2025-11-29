"""
Decorators for role-based access control and integration requirements.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(roles):
    """
    Decorator to check if user has one of the required roles.
    
    Args:
        roles: List of role strings (e.g., ['creator', 'manager'])
    
    Usage:
        @role_required(['creator'])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(
                    request, 
                    'You do not have permission to access this page. '
                    f'Required role(s): {", ".join(roles)}.'
                )
                return redirect('permission_denied')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def integration_required(service_type):
    """
    Decorator to check if user has connected the required integration.
    
    Args:
        service_type: String indicating the service ('google_drive' or 'youtube')
    
    Usage:
        @integration_required('google_drive')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            from integrations.models import Integration
            
            # Get the creator for this user
            creator = request.user.get_creator()
            
            # Check if the integration exists for the creator
            has_integration = Integration.objects.filter(
                user=creator,
                service_type=service_type
            ).exists()
            
            if not has_integration:
                service_name = service_type.replace('_', ' ').title()
                messages.error(
                    request,
                    f'{service_name} integration is not connected. '
                    f'Please connect {service_name} first.'
                )
                return redirect('integrations')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def creator_or_manager_required(view_func):
    """
    Decorator to check if user is a creator or manager.
    Convenience decorator for common permission pattern.
    """
    return role_required(['creator', 'manager'])(view_func)


def creator_only(view_func):
    """
    Decorator to check if user is a creator.
    Convenience decorator for creator-only views.
    """
    return role_required(['creator'])(view_func)
