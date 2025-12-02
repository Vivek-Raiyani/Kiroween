"""
URL configuration for A/B testing app.
"""
from django.urls import path
from . import views

app_name = 'abtesting'

urlpatterns = [
    # Test list and creation
    path('', views.abtest_list, name='test_list'),
    path('create/', views.create_abtest, name='create_test'),
    
    # Test detail and management
    path('<int:test_id>/', views.abtest_detail, name='test_detail'),
    path('<int:test_id>/manage/', views.abtest_management, name='test_management'),
    path('<int:test_id>/results/', views.abtest_results, name='test_results'),
]
