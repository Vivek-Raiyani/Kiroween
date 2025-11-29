# Design Document

## Overview

The Creator Backoffice Platform is a Django-based web application that provides content creators with a unified interface to manage their team, Google Drive files, and YouTube channel operations. The system implements role-based access control (RBAC) with three distinct roles: Creator, Manager, and Editor. The frontend uses Django templates with Bootstrap for styling and jQuery for dynamic interactions.

The architecture follows Django's MVT (Model-View-Template) pattern with clear separation between authentication, authorization, external API integrations, and business logic. The system integrates with Google Drive API for file management and YouTube Data API v3 for video uploads.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Browser                          │
│              (Django Templates + Bootstrap + jQuery)        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Django Application                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     Views    │  │  Middleware  │  │   Templates  │     │
│  │              │  │  (Auth/RBAC) │  │              │     │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘     │
│         │                  │                                │
│  ┌──────▼──────────────────▼───────┐  ┌──────────────┐    │
│  │         Business Logic          │  │   Services   │    │
│  │      (Models & Managers)        │  │              │    │
│  └──────┬──────────────────────────┘  └──────┬───────┘    │
│         │                                     │             │
│  ┌──────▼─────────────────────────────────────▼───────┐   │
│  │              Database (PostgreSQL/SQLite)          │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Google OAuth │  │ Google Drive │  │  YouTube API │
│     API      │  │     API      │  │      v3      │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Application Structure

```
creator_backoffice/
├── manage.py
├── config/                      # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/               # User authentication & management
│   │   ├── models.py          # User, Team models
│   │   ├── views.py           # Auth views
│   │   ├── forms.py           # Login, registration forms
│   │   └── decorators.py      # Role-based decorators
│   ├── integrations/          # External API integrations
│   │   ├── models.py          # OAuth credentials
│   │   ├── google_drive.py    # Drive API service
│   │   ├── youtube.py         # YouTube API service
│   │   └── views.py           # OAuth callback handlers
│   ├── files/                 # File management
│   │   ├── models.py          # File metadata cache
│   │   ├── views.py           # File listing, upload
│   │   └── services.py        # File operations
│   └── approvals/             # Approval workflow
│       ├── models.py          # ApprovalRequest model
│       ├── views.py           # Request management
│       └── services.py        # Approval logic
├── templates/
│   ├── base.html
│   ├── accounts/
│   ├── dashboard/
│   ├── files/
│   └── approvals/
└── static/
    ├── css/
    ├── js/
    └── img/
```

## Components and Interfaces

### 1. Authentication & Authorization Module

**Models:**
- `User` (extends Django's AbstractUser): email, role (Creator/Manager/Editor), creator_id (FK to creator)
- `Team`: creator (FK to User), members (M2M to User)
- `Integration`: user (FK), service_type (Drive/YouTube), access_token, refresh_token, expires_at

**Views:**
- `LoginView`: Handles user authentication
- `RegisterView`: Handles user registration via invitation
- `LogoutView`: Terminates user session
- `TeamManagementView`: Creator manages team members

**Decorators:**
- `@role_required(roles=[])`: Enforces role-based access
- `@integration_required(service)`: Ensures integration is connected

### 2. Integration Module

**Services:**
- `GoogleDriveService`:
  - `authenticate(code)`: Exchanges OAuth code for tokens
  - `list_files(query, page_token)`: Retrieves file metadata
  - `upload_file(file, metadata)`: Uploads file to Drive
  - `get_file(file_id)`: Retrieves specific file
  - `refresh_token()`: Refreshes expired access token

- `YouTubeService`:
  - `authenticate(code)`: Exchanges OAuth code for tokens
  - `get_channel_info()`: Retrieves channel details
  - `upload_video(file, title, description, privacy)`: Uploads video
  - `refresh_token()`: Refreshes expired access token

**Views:**
- `GoogleDriveConnectView`: Initiates OAuth flow
- `GoogleDriveCallbackView`: Handles OAuth callback
- `YouTubeConnectView`: Initiates OAuth flow
- `YouTubeCallbackView`: Handles OAuth callback
- `DisconnectIntegrationView`: Revokes integration

### 3. File Management Module

**Models:**
- `DriveFile`: file_id, name, mime_type, size, modified_time, file_url, creator (FK), cached_at

**Views:**
- `FileListView`: Displays Drive files with search
- `FileUploadView`: Handles file uploads to Drive
- `FileDetailView`: Shows file details and preview
 
**Services:**
- `FileService`:
  - `sync_files(user)`: Syncs Drive metadata to cache
  - `search_files(user, query)`: Searches cached files
  - `upload_file(user, file)`: Uploads via DriveService

### 4. Approval Workflow Module

**Models:**
- `ApprovalRequest`: 
  - editor (FK to User)
  - creator (FK to User)
  - file (FK to DriveFile)
  - description (TextField)
  - status (pending/approved/rejected)
  - reviewed_by (FK to User, nullable)
  - reviewed_at (DateTime, nullable)
  - rejection_reason (TextField, nullable)

**Views:**
- `CreateApprovalRequestView`: Editor submits request
- `ApprovalRequestListView`: Lists requests by role
- `ReviewApprovalRequestView`: Manager/Creator reviews
- `UploadToYouTubeView`: Manager/Creator uploads approved video

**Services:**
- `ApprovalService`:
  - `create_request(editor, file, description)`: Creates request
  - `approve_request(request, reviewer)`: Approves request
  - `reject_request(request, reviewer, reason)`: Rejects request
  - `notify_team(request, action)`: Sends notifications

### 5. Dashboard Module

**Views:**
- `DashboardView`: Role-based dashboard rendering
  - Editor: Recent files, pending requests, upload stats
  - Manager: Pending approvals, recent uploads, team activity
  - Creator: Team overview, integration status, platform stats

## Data Models

### User Model
```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ('creator', 'Creator'),
        ('manager', 'Manager'),
        ('editor', 'Editor'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    creator = models.ForeignKey('self', null=True, on_delete=models.CASCADE, related_name='team_members')
    invited_by = models.ForeignKey('self', null=True, on_delete=models.SET_NULL, related_name='invited_users')
    invitation_token = models.CharField(max_length=64, unique=True, null=True)
    invitation_accepted = models.BooleanField(default=False)
```

### Integration Model
```python
class Integration(models.Model):
    SERVICE_CHOICES = [
        ('google_drive', 'Google Drive'),
        ('youtube', 'YouTube'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'service_type']
```

### DriveFile Model
```python
class DriveFile(models.Model):
    file_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    modified_time = models.DateTimeField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    cached_at = models.DateTimeField(auto_now=True)
    web_view_link = models.URLField(null=True)
```

### ApprovalRequest Model
```python
class ApprovalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('uploaded', 'Uploaded'),
    ]
    editor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_requests')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    file = models.ForeignKey(DriveFile, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(null=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    youtube_video_id = models.CharField(max_length=20, null=True)
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Authentication & Authorization Properties

**Property 1: OAuth credential persistence**
*For any* successful OAuth authorization (Drive or YouTube), the system should store access tokens, refresh tokens, and expiration times in the database associated with the correct user.
**Validates: Requirements 1.2, 2.2**

**Property 2: Integration disconnection cleanup**
*For any* integration disconnection action, the system should revoke all stored credentials and remove access for all associated team members.
**Validates: Requirements 1.5, 2.5**

**Property 3: Role-based access enforcement**
*For any* user action, the system should verify the user's role permissions before execution, and prevent unauthorized actions with a permission denied message.
**Validates: Requirements 11.1, 11.2**

**Property 4: Permission updates on role change**
*For any* team member role modification, the system should immediately update their permissions to match the new role.
**Validates: Requirements 11.3**

**Property 5: Editor upload restriction**
*For any* editor user, attempting to upload directly to YouTube should be blocked and return a permission denied message.
**Validates: Requirements 6.5**

**Property 6: Creator full access**
*For any* creator user, all system features and operations should be accessible without restrictions.
**Validates: Requirements 9.1**

**Property 7: Session management**
*For any* successful login, the system should create a session, and for any logout, the system should terminate the session.
**Validates: Requirements 10.3, 10.5**

### Team Management Properties

**Property 8: Team member addition requirements**
*For any* team member addition attempt, the system should require both email address and role selection before allowing the operation.
**Validates: Requirements 3.1**

**Property 9: Invitation email delivery**
*For any* team member addition, the system should send an invitation email containing a unique registration link.
**Validates: Requirements 3.2**

**Property 10: Role assignment on registration**
*For any* team member registration via invitation, the system should assign the role specified in the invitation.
**Validates: Requirements 3.3**

**Property 11: Team list completeness**
*For any* creator viewing their team list, the system should display all team members with their assigned roles.
**Validates: Requirements 3.4**

**Property 12: Access revocation on removal**
*For any* team member removal, the system should immediately revoke all access permissions.
**Validates: Requirements 3.5**

### File Management Properties

**Property 13: File metadata display completeness**
*For any* file displayed in the Drive view, the system should include name, size, type, and modification date in the rendered output.
**Validates: Requirements 4.1**

**Property 14: Search result accuracy**
*For any* file search query, all returned results should match the search criteria.
**Validates: Requirements 4.2**

**Property 15: Editor delete prevention**
*For any* editor user attempting to delete a file, the system should prevent the action and display insufficient permissions message.
**Validates: Requirements 4.5**

**Property 16: File upload persistence**
*For any* file uploaded by an editor, the file should appear in the connected Google Drive and in the platform's file list.
**Validates: Requirements 5.2**

**Property 17: Upload success feedback**
*For any* successful file upload, the system should display a success confirmation and refresh the file list to include the new file.
**Validates: Requirements 5.3**

**Property 18: File size validation**
*For any* file upload attempt, the system should validate that the file size does not exceed the Drive quota before proceeding.
**Validates: Requirements 5.5**

### Approval Workflow Properties

**Property 19: Approval request requirements**
*For any* approval request creation attempt, the system should require video file selection (description is optional).
**Validates: Requirements 6.1**

**Property 20: Approval notification delivery**
*For any* approval request submission, the system should notify all managers and the creator.
**Validates: Requirements 6.2**

**Property 21: Initial request status**
*For any* newly created approval request, the system should set the status to "pending".
**Validates: Requirements 6.3**

**Property 22: Editor request visibility**
*For any* editor viewing their requests, the system should display all approval requests they submitted with current status.
**Validates: Requirements 6.4**

**Property 23: Manager pending request visibility**
*For any* manager accessing approval requests, the system should display all pending approval requests.
**Validates: Requirements 7.1**

**Property 24: Review information completeness**
*For any* approval request being reviewed, the system should display video file details and the editor's description.
**Validates: Requirements 7.2**

**Property 25: Approval status update and notification**
*For any* approval request approved by a manager or creator, the system should update the status to "approved" and notify the editor.
**Validates: Requirements 7.3**

**Property 26: Rejection requirements and notification**
*For any* approval request rejection, the system should require a rejection reason and notify the editor.
**Validates: Requirements 7.4**

**Property 27: Request history completeness**
*For any* manager or creator viewing request history, the system should display all approval requests with their decisions.
**Validates: Requirements 7.5**

### YouTube Upload Properties

**Property 28: Approved video filtering**
*For any* manager initiating YouTube upload, the system should display only videos with "approved" status.
**Validates: Requirements 8.1**

**Property 29: YouTube upload requirements**
*For any* YouTube upload attempt, the system should require video title, description, and privacy settings.
**Validates: Requirements 8.2**

**Property 30: Video upload execution**
*For any* confirmed YouTube upload by a manager or creator, the system should upload the video to the connected YouTube channel.
**Validates: Requirements 8.3**

**Property 31: Upload status update**
*For any* successful YouTube upload, the system should update the approval request status to "uploaded" and store the YouTube video ID.
**Validates: Requirements 8.4**

**Property 32: Creator direct upload**
*For any* creator user, uploading to YouTube should not require an approval request.
**Validates: Requirements 9.3**

### Dashboard Properties

**Property 33: Role-appropriate dashboard rendering**
*For any* user login, the system should display a dashboard that matches their role (editor/manager/creator).
**Validates: Requirements 12.1**

**Property 34: Editor dashboard completeness**
*For any* editor viewing their dashboard, the system should display recent files, pending requests, and upload statistics.
**Validates: Requirements 12.2**

**Property 35: Manager dashboard completeness**
*For any* manager viewing their dashboard, the system should display pending approvals, recent uploads, and team activity.
**Validates: Requirements 12.3**

**Property 36: Creator dashboard completeness**
*For any* creator viewing their dashboard, the system should display team overview, integration status, and platform statistics.
**Validates: Requirements 12.4**

## Error Handling

### OAuth Integration Errors
- **Token Expiration**: Implement automatic token refresh using refresh tokens before API calls
- **Authorization Failures**: Display user-friendly error messages and provide retry mechanism
- **API Rate Limits**: Implement exponential backoff and queue requests when rate limits are hit
- **Network Errors**: Catch connection errors and display appropriate messages to users

### File Operation Errors
- **Upload Failures**: Catch Drive API errors, rollback database changes, and inform user
- **Quota Exceeded**: Check quota before upload and display clear error message
- **Invalid File Types**: Validate file types on client and server side
- **Large Files**: Implement chunked uploads for files over 5MB

### Permission Errors
- **Unauthorized Access**: Return 403 Forbidden with clear message
- **Missing Integration**: Redirect to integration setup page with explanation
- **Invalid Tokens**: Trigger re-authentication flow
- **Session Expiration**: Redirect to login with session expired message

### Database Errors
- **Constraint Violations**: Catch unique constraint errors and display user-friendly messages
- **Connection Failures**: Implement connection pooling and retry logic
- **Transaction Failures**: Rollback transactions and log errors for debugging

### YouTube Upload Errors
- **Invalid Video Format**: Validate format before upload attempt
- **Upload Timeout**: Implement timeout handling and allow retry
- **Quota Exceeded**: Display daily upload limit message
- **Invalid Metadata**: Validate title, description length before API call


## Security Considerations

### Authentication & Authorization
- Use Django's built-in authentication system with secure password hashing (PBKDF2)
- Implement CSRF protection on all forms
- Use Django's permission system for role-based access control
- Implement session timeout (30 minutes of inactivity)
- Use HTTPS only in production (enforce with SECURE_SSL_REDIRECT)

### OAuth Token Storage
- Store tokens encrypted in database using Django's `cryptography` library
- Never expose tokens in logs or error messages
- Implement token rotation and automatic refresh
- Store refresh tokens separately from access tokens
- Use environment variables for OAuth client secrets

### API Security
- Validate all user inputs on server side
- Implement rate limiting on API endpoints (django-ratelimit)
- Use Django's built-in SQL injection protection (ORM)
- Sanitize file uploads (validate MIME types, scan for malware)
- Implement CORS properly if adding API endpoints

### Data Privacy
- Only store necessary file metadata, not file contents
- Implement audit logging for sensitive operations
- Allow users to delete their data (GDPR compliance)
- Use Django's built-in XSS protection in templates
- Implement proper error handling to avoid information leakage

## Deployment Considerations

### Environment Setup
- Use environment variables for sensitive configuration (`.env` file)
- Separate settings for development, staging, and production
- Use PostgreSQL in production (SQLite for development)
- Configure static file serving (WhiteNoise or CDN)
- Set up proper logging (file-based in production)

### Dependencies
```
Django==4.2
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.100.0
python-decouple==3.8
psycopg2-binary==2.9.9
hypothesis==6.92.0
django-ratelimit==4.1.0
cryptography==41.0.5
```

### Performance Optimization
- Implement database indexing on foreign keys and frequently queried fields
- Use Django's select_related and prefetch_related for query optimization
- Cache Drive file metadata (refresh every 5 minutes)
- Implement pagination for file lists and approval requests
- Use Django's caching framework for dashboard statistics

### Monitoring & Logging
- Log all OAuth operations (success/failure)
- Log all permission denied attempts
- Log all file uploads and YouTube uploads
- Monitor API rate limit usage
- Set up error tracking (Sentry or similar)
- Monitor database query performance

## Future Enhancements

- Real-time notifications using WebSockets (Django Channels)
- Bulk video upload capability
- Video thumbnail preview in file list
- Advanced search with filters (date range, file type, uploader)
- Analytics dashboard with upload trends
- Multi-language support
- Mobile responsive design improvements
- Video editing metadata (tags, categories, playlists)
- Scheduled video publishing
- Team activity feed with real-time updates
