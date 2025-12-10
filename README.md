# Creator Backoffice Platform

A Django-based web application that enables content creators to manage their team operations, Google Drive files, and YouTube channel uploads through a unified interface with role-based permissions.

## Features

- **Role-Based Access Control**: Three distinct roles (Creator, Manager, Editor) with specific permissions
- **Google Drive Integration**: Connect and manage files from Google Drive with automatic sync
- **YouTube Integration**: Upload approved videos directly to YouTube channel
- **Team Management**: Add and manage team members with different roles via email invitations
- **Approval Workflow**: Editors submit requests, managers/creators approve, with email notifications
- **Creator Direct Upload**: Creators can upload videos directly to YouTube without approval
- **Dashboard**: Role-specific dashboards with relevant statistics and information
- **Comprehensive Error Handling**: User-friendly error messages with automatic recovery mechanisms
- **Secure Token Management**: Encrypted OAuth token storage with automatic refresh

## Project Structure

```
creator_backoffice/
├── config/                 # Django project settings
├── accounts/              # User authentication & management
├── integrations/          # Google Drive & YouTube API integrations
├── files/                 # File management functionality
├── approvals/             # Approval workflow
├── dashboard/             # Role-based dashboards
├── templates/             # HTML templates
├── static/                # CSS, JavaScript, images
└── manage.py              # Django management script
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. Clone the repository and navigate to the project directory

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your configuration:
   - Set a secure `SECRET_KEY`
   - Configure Google OAuth credentials
   - Adjust other settings as needed

6. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```

8. Run the development server:
   ```bash
   python manage.py runserver
   ```

9. Access the application at `http://localhost:8000`

## Google OAuth Setup

### Option 1: Separate OAuth Clients (Recommended)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable Google Drive API and YouTube Data API v3
4. Create two separate OAuth 2.0 credentials:
   - **Google Drive Client**: For Drive file management
   - **YouTube Client**: For YouTube uploads
5. Add authorized redirect URIs:
   - Drive: `http://localhost:8000/integrations/google-drive/callback/`
   - YouTube: `http://localhost:8000/integrations/youtube/callback/`
6. Copy credentials to your `.env` file:
   ```
   GOOGLE_DRIVE_CLIENT_ID=your_drive_client_id
   GOOGLE_DRIVE_CLIENT_SECRET=your_drive_client_secret
   YOUTUBE_CLIENT_ID=your_youtube_client_id
   YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
   ```

### Option 2: Single OAuth Client

If you prefer using one OAuth client for both services:

1. Create a single OAuth 2.0 credential with both Drive and YouTube scopes
2. Add both redirect URIs to the same client
3. Use the same credentials for both services in `.env`:
   ```
   GOOGLE_DRIVE_CLIENT_ID=your_client_id
   GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret
   YOUTUBE_CLIENT_ID=your_client_id
   YOUTUBE_CLIENT_SECRET=your_client_secret
   ```

**Note**: When using a single OAuth client, disconnecting one service will not revoke the token to avoid breaking the other service. Users can revoke access from their Google Account settings if needed.


## Technology Stack

- **Backend**: Django 4.2
- **Frontend**: Bootstrap 5.3, jQuery 3.7
- **APIs**: Google Drive API, YouTube Data API v3
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Django built-in auth with custom User model




## Email Setting

Currently the app can work without email configuration for adding team member 

To use mail for team member adding follow below steps:
`
accounts/views.py

method : add_team_member_view

uncomment below line:
send_invitation_email(email, invitation_url, creator, role)
`

# License

MIT License

Copyright (c) 2025 Vivek

Permission is hereby granted, free of charge, to any person
