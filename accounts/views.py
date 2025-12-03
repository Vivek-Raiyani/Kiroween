from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .forms import LoginForm, RegistrationForm, AddTeamMemberForm, CreatorRegistrationForm
from .models import User, Team
from .decorators import role_required


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Redirect to next parameter or dashboard
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout."""
    username = request.user.username
    logout(request)
    messages.success(request, f'Goodbye, {username}! You have been logged out.')
    return redirect('accounts:login')


@require_http_methods(["GET", "POST"])
def creator_register_view(request):
    """Handle creator self-registration (no invitation required)."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CreatorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log the user in automatically
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your creator account has been created.')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CreatorRegistrationForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/creator_register.html', context)


@require_http_methods(["GET", "POST"])
def register_view(request, token=None):
    """Handle user registration via invitation token."""
    # Check if token is valid
    if token:
        try:
            invited_user = User.objects.get(invitation_token=token, invitation_accepted=False)
        except User.DoesNotExist:
            messages.error(request, 'Invalid or expired invitation token.')
            return redirect('accounts:login')
    else:
        messages.error(request, 'Registration requires an invitation.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST, invitation_token=token)
        if form.is_valid():
            user = form.save()
            
            # Log the user in automatically
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistrationForm(invitation_token=token)
    
    context = {
        'form': form,
        'token': token,
        'invited_user': invited_user if token else None
    }
    
    return render(request, 'accounts/register.html', context)



@login_required
@role_required(['creator'])
def team_management_view(request):
    """Display team management page for creators."""
    creator = request.user
    
    # Get or create team for this creator
    team, created = Team.objects.get_or_create(creator=creator)
    
    # Get all team members
    team_members = User.objects.filter(creator=creator).order_by('role', 'username')
    
    # Get pending invitations (users with invitation tokens that haven't been accepted)
    pending_invitations = User.objects.filter(
        invited_by=creator,
        invitation_accepted=False
    ).order_by('-id')

    # Add invitation URLs to context
    invitations_with_links = [
        {
            'email': user.email,
            'role': user.role,
            'invitation_url': request.build_absolute_uri(
                reverse('accounts:register', kwargs={'token': user.invitation_token})
            ),
            'date_joined': user.date_joined,
            'id': user.id
        }
        for user in pending_invitations
    ]
    print(invitations_with_links)
    
    context = {
        'team': team,
        'team_members': team_members,
        'pending_invitations': invitations_with_links,
    }
    
    return render(request, 'accounts/team_management.html', context)


@login_required
@role_required(['creator'])
@require_http_methods(["GET", "POST"])
def add_team_member_view(request):
    """Handle adding a new team member."""
    if request.method == 'POST':
        form = AddTeamMemberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            creator = request.user
            
            # Check if user with this email already exists in the team
            existing_user = User.objects.filter(email=email, creator=creator).first()
            if existing_user:
                messages.error(request, f'A user with email {email} is already in your team.')
                return redirect('accounts:team_management')
            
            # Check if there's already a pending invitation for this email
            pending_invitation = User.objects.filter(
                email=email,
                invited_by=creator,
                invitation_accepted=False
            ).first()
            
            if pending_invitation:
                messages.warning(request, f'An invitation has already been sent to {email}.')
                return redirect('accounts:team_management')
            
            # Generate invitation token
            invitation_token = User.generate_invitation_token()
            
            # Create a placeholder user with invitation token
            invited_user = User.objects.create(
                username=f'invited_{invitation_token[:8]}',  # Temporary username
                email=email,
                role=role,
                creator=creator,
                invited_by=creator,
                invitation_token=invitation_token,
                invitation_accepted=False,
                is_active=False  # Not active until they register
            )
            
            # Send invitation email
            invitation_url = request.build_absolute_uri(
                reverse('accounts:register', kwargs={'token': invitation_token})
            )
            
            try:
                # send_invitation_email(email, invitation_url, creator, role)
                messages.success(request, f'Invitation sent to {email} successfully!')
            except Exception as e:
                # If email fails, still show success but log the error
                messages.warning(request, f'Invitation created for {email}, but email delivery may have failed. Share this link: {invitation_url}')
                print(f"Email error: {e}")
            
            return redirect('accounts:team_management')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = AddTeamMemberForm()
    
    return render(request, 'accounts/add_team_member.html', {'form': form})


@login_required
@role_required(['creator'])
@require_http_methods(["POST"])
def remove_team_member_view(request, user_id):
    """Handle removing a team member."""
    creator = request.user
    
    # Get the user to remove
    user_to_remove = get_object_or_404(User, id=user_id)
    
    # Verify this user belongs to the creator's team
    if user_to_remove.creator != creator and user_to_remove.invited_by != creator:
        messages.error(request, 'You can only remove members from your own team.')
        return redirect('accounts:team_management')
    
    # Prevent removing yourself
    if user_to_remove == creator:
        messages.error(request, 'You cannot remove yourself from the team.')
        return redirect('accounts:team_management')
    
    # Store username for message
    username = user_to_remove.username if user_to_remove.invitation_accepted else user_to_remove.email
    
    # Remove from team and delete user
    user_to_remove.delete()
    
    messages.success(request, f'{username} has been removed from your team.')
    return redirect('accounts:team_management')


def send_invitation_email(email, invitation_url, creator, role):
    """Send invitation email to new team member."""
    subject = f'Invitation to join {creator.username}\'s team on Creator Backoffice'
    
    message = f"""
Hello,

{creator.username} has invited you to join their team on Creator Backoffice Platform as a {role.title()}.

To accept this invitation and create your account, please click the link below:

{invitation_url}

This invitation link is unique to you and can only be used once.

If you did not expect this invitation, you can safely ignore this email.

Best regards,
Creator Backoffice Platform Team
"""
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creatorbackoffice.com')
    print("-"*40)
    print("Starting enail sending process for new user ")
    try:
        send_mail(
            subject,
            message,
            from_email,
            [email],
            fail_silently=False,
        )
        
        print("Email send sucessfuull right now")
    except Exception as e:
        print("Error occurred while sending email:", e)



@login_required
def permission_denied_view(request):
    """Display permission denied error page."""
    context = {
        'user': request.user,
        'user_role': request.user.get_role_display(),
    }
    return render(request, 'accounts/permission_denied.html', context, status=403)


# accounts/views.py
# accounts/views.py
import logging
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings

# Create a logger for this module
logger = logging.getLogger(__name__)

def test_email_view(request):
    """
    Test if Django email is working.
    Sends a test email to the address specified in the 'to' GET parameter.
    Logs each step and any errors for debugging.
    """
    to_email = 'vivek16903@gmail.com'
    subject = "Render Email Test"
    message = "Hello! This is a test email from your Django app running on Render."
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

    logger.info("Starting test_email_view")
    logger.info(f"From: {from_email}, To: {to_email}, Subject: {subject}")

    try:
        result = send_mail(
            subject,
            message,
            from_email,
            [to_email],
            fail_silently=False,
        )
        logger.info(f"send_mail returned: {result}")
        return HttpResponse(f"Test email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send test email: {e}", exc_info=True)
        return HttpResponse(f"Failed to send test email: {e}")
