from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    path('create/', views.create_approval_request, name='create_request'),
    path('requests/', views.approval_request_list, name='request_list'),
    path('pending/', views.pending_approvals, name='pending_approvals'),
    path('request/<int:pk>/', views.approval_request_detail, name='request_detail'),
    path('request/<int:pk>/approve/', views.approve_request, name='approve_request'),
    path('request/<int:pk>/reject/', views.reject_request, name='reject_request'),
    path('history/', views.request_history, name='request_history'),
    path('youtube/upload/', views.youtube_upload_list, name='youtube_upload_list'),
    path('youtube/upload/<int:pk>/', views.youtube_upload, name='youtube_upload'),
    path('creator/direct-upload/', views.creator_direct_upload, name='creator_direct_upload'),
]
