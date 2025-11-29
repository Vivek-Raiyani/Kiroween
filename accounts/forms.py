from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import EmailValidator
from .models import User, Team


class AddTeamMemberForm(forms.Form):
    """Form for adding a team member with email and role selection."""
    
    email = forms.EmailField(
        required=True,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        }),
        help_text='Enter the email address of the person you want to invite'
    )
    
    role = forms.ChoiceField(
        required=True,
        choices=[
            ('manager', 'Manager'),
            ('editor', 'Editor'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text='Select the role for this team member'
    )


class LoginForm(AuthenticationForm):
    """Custom login form with Bootstrap styling."""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class CreatorRegistrationForm(UserCreationForm):
    """Registration form for creators (self-signup)."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'creator'  # Always set role to creator
        user.creator = None  # Creators don't have a creator
        
        if commit:
            user.save()
            # Create a team for this creator
            Team.objects.create(creator=user)
        
        return user


class RegistrationForm(UserCreationForm):
    """Custom registration form for invitation-based signup."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        self.invitation_token = kwargs.pop('invitation_token', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        # If there's an invitation token, link the user
        if self.invitation_token:
            try:
                invited_user = User.objects.get(invitation_token=self.invitation_token)
                user.role = invited_user.role
                user.creator = invited_user.creator
                user.invited_by = invited_user.invited_by
                user.invitation_accepted = True
                
                if commit:
                    user.save()
                    # Delete the invitation placeholder
                    invited_user.delete()
            except User.DoesNotExist:
                pass
        
        if commit:
            user.save()
        
        return user
