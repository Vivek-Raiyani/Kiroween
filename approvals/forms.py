"""
Forms for approval request workflow.
"""
from django import forms
from .models import ApprovalRequest
from files.models import DriveFile


class ApprovalRequestForm(forms.ModelForm):
    """Form for creating approval requests."""
    
    class Meta:
        model = ApprovalRequest
        fields = ['file', 'description']
        widgets = {
            'file': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Optional: Add notes or description about this video...'
            }),
        }
        labels = {
            'file': 'Select Video File',
            'description': 'Description (Optional)',
        }
        help_texts = {
            'file': 'Choose a video file from Google Drive to request approval for upload',
            'description': 'Provide any additional context or notes for the reviewer',
        }
    
    def __init__(self, user, *args, **kwargs):
        """Initialize form with user-specific file queryset."""
        super().__init__(*args, **kwargs)
        
        # Get the creator for this user
        creator = user.get_creator()
        
        # Filter files to only show video files from the creator's Drive
        video_mime_types = [
            'video/mp4',
            'video/mpeg',
            'video/quicktime',
            'video/x-msvideo',
            'video/x-matroska',
            'video/webm',
        ]
        
        self.fields['file'].queryset = DriveFile.objects.filter(
            creator=creator,
            mime_type__in=video_mime_types
        ).order_by('-modified_time')
        
        # Update the empty label
        self.fields['file'].empty_label = "-- Select a video file --"


class RejectRequestForm(forms.Form):
    """Form for rejecting approval requests with a reason."""
    
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Please provide a detailed reason for rejecting this request...',
            'required': True
        }),
        label='Rejection Reason',
        help_text='Explain why this request is being rejected so the editor can make improvements',
        required=True
    )


class CreatorDirectUploadForm(forms.Form):
    """Form for creators to upload videos directly to YouTube without approval."""
    
    SOURCE_CHOICES = [
        ('drive', 'Select from Google Drive'),
        ('upload', 'Upload new file'),
    ]
    
    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Video Source',
        initial='drive',
        help_text='Choose whether to select an existing file from Drive or upload a new one'
    )
    
    drive_file = forms.ModelChoiceField(
        queryset=DriveFile.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Select Video from Drive',
        empty_label='-- Select a video file --',
        help_text='Choose a video file from your Google Drive'
    )
    
    upload_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'video/*'
        }),
        label='Upload Video File',
        help_text='Upload a video file from your computer'
    )
    
    title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a compelling title for your video',
            'required': True
        }),
        label='Video Title',
        help_text='Maximum 100 characters'
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Provide a detailed description of your video content',
            'required': True,
            'maxlength': '5000'
        }),
        label='Video Description',
        help_text='Maximum 5000 characters. This will be visible to viewers on YouTube.'
    )
    
    privacy_status = forms.ChoiceField(
        choices=[
            ('private', 'Private - Only you and people you choose can watch'),
            ('unlisted', 'Unlisted - Anyone with the link can watch'),
            ('public', 'Public - Everyone can watch'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Privacy Status',
        initial='private',
        help_text='You can change this later in YouTube Studio'
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'tag1, tag2, tag3'
        }),
        label='Tags (Optional)',
        help_text='Separate tags with commas. Tags help viewers find your video.'
    )
    
    def __init__(self, user, *args, **kwargs):
        """Initialize form with user-specific file queryset."""
        super().__init__(*args, **kwargs)
        
        # Filter files to only show video files from the creator's Drive
        video_mime_types = [
            'video/mp4',
            'video/mpeg',
            'video/quicktime',
            'video/x-msvideo',
            'video/x-matroska',
            'video/webm',
        ]
        
        self.fields['drive_file'].queryset = DriveFile.objects.filter(
            creator=user,
            mime_type__in=video_mime_types
        ).order_by('-modified_time')
    
    def clean(self):
        """Validate that either drive_file or upload_file is provided based on source."""
        cleaned_data = super().clean()
        source = cleaned_data.get('source')
        drive_file = cleaned_data.get('drive_file')
        upload_file = cleaned_data.get('upload_file')
        
        if source == 'drive' and not drive_file:
            raise forms.ValidationError('Please select a video file from Google Drive.')
        
        if source == 'upload' and not upload_file:
            raise forms.ValidationError('Please upload a video file.')
        
        # Validate file type for uploaded files
        if source == 'upload' and upload_file:
            # Check if it's a video file
            content_type = upload_file.content_type
            if not content_type or not content_type.startswith('video/'):
                raise forms.ValidationError('Please upload a valid video file.')
        
        return cleaned_data
