"""
URL configuration for analytics app.
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('video/<str:video_id>/', views.video_analytics, name='video_analytics'),
    path('channel/', views.channel_analytics, name='channel_analytics'),
    path('competitors/', views.competitor_analysis, name='competitor_analysis'),
    path('seo/', views.seo_insights, name='seo_insights'),
    path('posting/', views.posting_recommendations, name='posting_recommendations'),
    # Export endpoints
    path('export/video/<str:video_id>/csv/', views.export_video_metrics_csv, name='export_video_csv'),
    path('export/video/<str:video_id>/pdf/', views.export_video_metrics_pdf, name='export_video_pdf'),
    path('export/channel/csv/', views.export_channel_metrics_csv, name='export_channel_csv'),
    path('export/channel/pdf/', views.export_channel_metrics_pdf, name='export_channel_pdf'),
]
