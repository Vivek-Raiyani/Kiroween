from django.db import models
from django.contrib.auth.models import AbstractUser
import secrets


class User(AbstractUser):
    """Custom User model with role-based access control."""
    
    ROLE_CHOICES = [
        ('creator', 'Creator'),
        ('manager', 'Manager'),
        ('editor', 'Editor'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='editor',
        help_text='User role determines access permissions'
    )
    
    creator = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='team_members',
        help_text='The creator this user belongs to (null for creators themselves)'
    )
    
    invited_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='invited_users',
        help_text='The user who invited this user'
    )
    
    invitation_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text='Unique token for invitation acceptance'
    )
    
    invitation_accepted = models.BooleanField(
        default=False,
        help_text='Whether the invitation has been accepted'
    )
    
    class Meta:
        ordering = ['username']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_creator(self):
        """Check if user is a creator."""
        return self.role == 'creator'
    
    def is_manager(self):
        """Check if user is a manager."""
        return self.role == 'manager'
    
    def is_editor(self):
        """Check if user is an editor."""
        return self.role == 'editor'
    
    def get_creator(self):
        """Get the creator for this user (self if creator, otherwise the creator FK)."""
        if self.is_creator():
            return self
        return self.creator
    
    @staticmethod
    def generate_invitation_token():
        """Generate a unique invitation token."""
        return secrets.token_urlsafe(48)


class Team(models.Model):
    """Team model for managing team relationships."""
    
    creator = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='team',
        help_text='The creator who owns this team'
    )
    
    members = models.ManyToManyField(
        User,
        related_name='teams',
        blank=True,
        help_text='Team members (managers and editors)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Team of {self.creator.username}"
    
    def add_member(self, user):
        """Add a member to the team."""
        if user != self.creator:
            self.members.add(user)
    
    def remove_member(self, user):
        """Remove a member from the team."""
        self.members.remove(user)
    
    def get_all_members(self):
        """Get all team members including the creator."""
        return [self.creator] + list(self.members.all())
