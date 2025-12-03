from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.creator_register_view, name='creator_register'),
    path('register/<str:token>/', views.register_view, name='register'),
    path('team/', views.team_management_view, name='team_management'),
    path('team/add/', views.add_team_member_view, name='add_team_member'),
    path('team/remove/<int:user_id>/', views.remove_team_member_view, name='remove_team_member'),
    path('permission-denied/', views.permission_denied_view, name='permission_denied'),

    path('test-email/', views.test_email_view, name='test_email'),
]
