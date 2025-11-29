from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    path('', views.integrations_dashboard, name='dashboard'),
    
    # Google Drive OAuth
    path('google-drive/connect/', views.google_drive_connect, name='google_drive_connect'),
    path('google-drive/callback/', views.google_drive_callback, name='google_drive_callback'),
    path('google-drive/disconnect/', views.google_drive_disconnect, name='google_drive_disconnect'),
    path('google-drive/status/', views.google_drive_status, name='google_drive_status'),
    
    # YouTube OAuth
    path('youtube/connect/', views.youtube_connect, name='youtube_connect'),
    path('youtube/callback/', views.youtube_callback, name='youtube_callback'),
    path('youtube/disconnect/', views.youtube_disconnect, name='youtube_disconnect'),
    path('youtube/status/', views.youtube_status, name='youtube_status'),
]
