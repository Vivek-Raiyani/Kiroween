"""
Context processors for adding user role information to all templates.
"""


def user_role(request):
    """
    Add user role information to template context.
    
    This makes role checking easier in templates without repeating logic.
    """
    if request.user.is_authenticated:
        return {
            'is_creator': request.user.role == 'creator',
            'is_manager': request.user.role == 'manager',
            'is_editor': request.user.role == 'editor',
            'is_creator_or_manager': request.user.role in ['creator', 'manager'],
        }
    return {
        'is_creator': False,
        'is_manager': False,
        'is_editor': False,
        'is_creator_or_manager': False,
    }
