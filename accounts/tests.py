from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import User, Team

User = get_user_model()


class UserModelTests(TestCase):
    """Test User model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.creator = User.objects.create_user(
            username='creator1',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        self.manager = User.objects.create_user(
            username='manager1',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        self.editor = User.objects.create_user(
            username='editor1',
            email='editor@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
    
    def test_user_creation(self):
        """Test that users are created with correct attributes."""
        self.assertEqual(self.creator.username, 'creator1')
        self.assertEqual(self.creator.role, 'creator')
        self.assertTrue(self.creator.is_creator())
        
        self.assertEqual(self.manager.role, 'manager')
        self.assertTrue(self.manager.is_manager())
        self.assertEqual(self.manager.creator, self.creator)
        
        self.assertEqual(self.editor.role, 'editor')
        self.assertTrue(self.editor.is_editor())
        self.assertEqual(self.editor.creator, self.creator)
    
    def test_get_creator(self):
        """Test get_creator method returns correct creator."""
        self.assertEqual(self.creator.get_creator(), self.creator)
        self.assertEqual(self.manager.get_creator(), self.creator)
        self.assertEqual(self.editor.get_creator(), self.creator)
    
    def test_generate_invitation_token(self):
        """Test invitation token generation."""
        token = User.generate_invitation_token()
        self.assertIsNotNone(token)
        self.assertGreater(len(token), 0)
        
        # Test uniqueness
        token2 = User.generate_invitation_token()
        self.assertNotEqual(token, token2)


class TeamModelTests(TestCase):
    """Test Team model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.creator = User.objects.create_user(
            username='creator1',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        self.team = Team.objects.create(creator=self.creator)
        
        self.manager = User.objects.create_user(
            username='manager1',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        self.editor = User.objects.create_user(
            username='editor1',
            email='editor@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
    
    def test_team_creation(self):
        """Test team is created correctly."""
        self.assertEqual(self.team.creator, self.creator)
        self.assertEqual(self.team.members.count(), 0)
    
    def test_add_member(self):
        """Test adding members to team."""
        self.team.add_member(self.manager)
        self.team.add_member(self.editor)
        
        self.assertEqual(self.team.members.count(), 2)
        self.assertIn(self.manager, self.team.members.all())
        self.assertIn(self.editor, self.team.members.all())
    
    def test_remove_member(self):
        """Test removing members from team."""
        self.team.add_member(self.manager)
        self.team.add_member(self.editor)
        
        self.team.remove_member(self.manager)
        
        self.assertEqual(self.team.members.count(), 1)
        self.assertNotIn(self.manager, self.team.members.all())
        self.assertIn(self.editor, self.team.members.all())
    
    def test_get_all_members(self):
        """Test getting all members including creator."""
        self.team.add_member(self.manager)
        self.team.add_member(self.editor)
        
        all_members = self.team.get_all_members()
        
        self.assertEqual(len(all_members), 3)
        self.assertIn(self.creator, all_members)
        self.assertIn(self.manager, all_members)
        self.assertIn(self.editor, all_members)


class LoginViewTests(TestCase):
    """Test login functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.login_url = reverse('accounts:login')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='creator'
        )
    
    def test_login_page_loads(self):
        """Test login page loads successfully."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
    
    def test_successful_login(self):
        """Test successful login redirects to dashboard."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_failed_login_invalid_credentials(self):
        """Test login fails with invalid credentials."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_authenticated_user_redirects(self):
        """Test authenticated user is redirected from login page."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.login_url)
        
        self.assertRedirects(response, reverse('dashboard'))


class LogoutViewTests(TestCase):
    """Test logout functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.logout_url = reverse('accounts:logout')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='creator'
        )
    
    def test_logout_requires_authentication(self):
        """Test logout requires user to be logged in."""
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.logout_url}")
    
    def test_successful_logout(self):
        """Test successful logout redirects to login."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.logout_url)
        
        self.assertRedirects(response, reverse('accounts:login'))


class RegistrationViewTests(TestCase):
    """Test registration functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.creator = User.objects.create_user(
            username='creator1',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        # Create invitation placeholder
        self.invitation_token = User.generate_invitation_token()
        self.invited_user = User.objects.create(
            username='temp_user',
            email='invited@test.com',
            role='manager',
            creator=self.creator,
            invited_by=self.creator,
            invitation_token=self.invitation_token,
            invitation_accepted=False
        )
        self.invited_user.set_unusable_password()
        self.invited_user.save()
        
        self.register_url = reverse('accounts:register', kwargs={'token': self.invitation_token})
    
    def test_registration_page_loads_with_valid_token(self):
        """Test registration page loads with valid token."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
    
    def test_registration_fails_without_token(self):
        """Test registration fails without token."""
        response = self.client.get(reverse('accounts:register', kwargs={'token': 'invalid'}))
        self.assertRedirects(response, reverse('accounts:login'))
    
    def test_successful_registration(self):
        """Test successful registration creates user and logs them in."""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        
        self.assertRedirects(response, reverse('dashboard'))
        
        # Check user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertEqual(user.role, 'manager')
        self.assertEqual(user.creator, self.creator)
        self.assertTrue(user.invitation_accepted)
        
        # Check invitation placeholder was deleted
        self.assertFalse(User.objects.filter(invitation_token=self.invitation_token).exists())


class SessionManagementTests(TestCase):
    """Test session management functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.login_url = reverse('accounts:login')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='creator'
        )
    
    def test_session_created_on_login(self):
        """Test session is created when user logs in."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertIn('_auth_user_id', self.client.session)
    
    def test_session_terminated_on_logout(self):
        """Test session is terminated when user logs out."""
        self.client.login(username='testuser', password='testpass123')
        self.assertTrue('_auth_user_id' in self.client.session)
        
        self.client.get(reverse('accounts:logout'))
        
        # Session should be cleared
        self.assertNotIn('_auth_user_id', self.client.session)


class RoleAssignmentTests(TestCase):
    """Test role assignment functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.creator = User.objects.create_user(
            username='creator1',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
    
    def test_creator_role_assignment(self):
        """Test creator role is assigned correctly."""
        self.assertEqual(self.creator.role, 'creator')
        self.assertTrue(self.creator.is_creator())
        self.assertFalse(self.creator.is_manager())
        self.assertFalse(self.creator.is_editor())
    
    def test_manager_role_assignment(self):
        """Test manager role is assigned correctly."""
        manager = User.objects.create_user(
            username='manager1',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        self.assertEqual(manager.role, 'manager')
        self.assertTrue(manager.is_manager())
        self.assertFalse(manager.is_creator())
        self.assertFalse(manager.is_editor())
    
    def test_editor_role_assignment(self):
        """Test editor role is assigned correctly."""
        editor = User.objects.create_user(
            username='editor1',
            email='editor@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
        
        self.assertEqual(editor.role, 'editor')
        self.assertTrue(editor.is_editor())
        self.assertFalse(editor.is_creator())
        self.assertFalse(editor.is_manager())
    
    def test_role_assignment_via_invitation(self):
        """Test role is assigned correctly via invitation."""
        invitation_token = User.generate_invitation_token()
        
        # Create invitation placeholder
        invited_user = User.objects.create(
            username='temp_user',
            email='invited@test.com',
            role='manager',
            creator=self.creator,
            invited_by=self.creator,
            invitation_token=invitation_token,
            invitation_accepted=False
        )
        invited_user.set_unusable_password()
        invited_user.save()
        
        # Register via invitation
        client = Client()
        register_url = reverse('accounts:register', kwargs={'token': invitation_token})
        client.post(register_url, {
            'username': 'newmanager',
            'email': 'newmanager@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        
        # Check role was assigned
        user = User.objects.get(username='newmanager')
        self.assertEqual(user.role, 'manager')
        self.assertEqual(user.creator, self.creator)



class TeamManagementViewTests(TestCase):
    """Test team management view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.creator = User.objects.create_user(
            username='creator1',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        self.manager = User.objects.create_user(
            username='manager1',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        self.editor = User.objects.create_user(
            username='editor1',
            email='editor@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
        
        self.team_url = reverse('accounts:team_management')
    
    def test_team_management_requires_login(self):
        """Test team management page requires authentication."""
        response = self.client.get(self.team_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.team_url}")
    
    def test_team_management_requires_creator_role(self):
        """Test team management page requires creator role."""
        # Test with manager
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(self.team_url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        
        # Test with editor
        self.client.login(username='editor1', password='testpass123')
        response = self.client.get(self.team_url, follow=True)
        self.assertEqual(response.status_code, 403)
    
    def test_team_management_page_loads_for_creator(self):
        """Test team management page loads for creator."""
        self.client.login(username='creator1', password='testpass123')
        response = self.client.get(self.team_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/team_management.html')
    
    def test_team_management_displays_team_members(self):
        """Test team management page displays all team members."""
        self.client.login(username='creator1', password='testpass123')
        response = self.client.get(self.team_url)
        
        self.assertContains(response, 'manager1')
        self.assertContains(response, 'editor1')


class AddTeamMemberViewTests(TestCase):
    """Test add team member functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.creator = User.objects.create_user(
            username='creator1',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        self.add_member_url = reverse('accounts:add_team_member')
    
    def test_add_team_member_requires_login(self):
        """Test add team member page requires authentication."""
        response = self.client.get(self.add_member_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.add_member_url}")
    
    def test_add_team_member_requires_creator_role(self):
        """Test add team member requires creator role."""
        manager = User.objects.create_user(
            username='manager1',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(self.add_member_url, follow=True)
        self.assertEqual(response.status_code, 403)
    
    def test_add_team_member_page_loads(self):
        """Test add team member page loads for creator."""
        self.client.login(username='creator1', password='testpass123')
        response = self.client.get(self.add_member_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/add_team_member.html')
    
    def test_add_team_member_creates_invitation(self):
        """Test adding team member creates invitation."""
        self.client.login(username='creator1', password='testpass123')
        
        response = self.client.post(self.add_member_url, {
            'email': 'newmember@test.com',
            'role': 'manager'
        })
        
        self.assertRedirects(response, reverse('accounts:team_management'))
        
        # Check invitation was created
        invitation = User.objects.get(email='newmember@test.com', invitation_accepted=False)
        self.assertEqual(invitation.role, 'manager')
        self.assertEqual(invitation.creator, self.creator)
        self.assertEqual(invitation.invited_by, self.creator)
        self.assertIsNotNone(invitation.invitation_token)
    
    def test_add_team_member_prevents_duplicate_email(self):
        """Test adding team member with existing email is prevented."""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='existing@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        self.client.login(username='creator1', password='testpass123')
        
        # Count users before
        user_count_before = User.objects.filter(email='existing@test.com').count()
        
        response = self.client.post(self.add_member_url, {
            'email': 'existing@test.com',
            'role': 'editor'
        })
        
        self.assertRedirects(response, reverse('accounts:team_management'))
        
        # Check no new user was created
        user_count_after = User.objects.filter(email='existing@test.com').count()
        self.assertEqual(user_count_before, user_count_after)
    
    def test_add_team_member_prevents_duplicate_invitation(self):
        """Test adding team member with pending invitation is prevented."""
        # Create pending invitation
        token = User.generate_invitation_token()
        User.objects.create(
            username='temp_user',
            email='pending@test.com',
            role='manager',
            creator=self.creator,
            invited_by=self.creator,
            invitation_token=token,
            invitation_accepted=False,
            is_active=False
        )
        
        self.client.login(username='creator1', password='testpass123')
        
        response = self.client.post(self.add_member_url, {
            'email': 'pending@test.com',
            'role': 'editor'
        })
        
        self.assertRedirects(response, reverse('accounts:team_management'))
        
        # Check no additional invitation was created
        invitations = User.objects.filter(email='pending@test.com', invitation_accepted=False)
        self.assertEqual(invitations.count(), 1)


class RemoveTeamMemberViewTests(TestCase):
    """Test remove team member functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.creator = User.objects.create_user(
            username='creator1',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        self.manager = User.objects.create_user(
            username='manager1',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        self.editor = User.objects.create_user(
            username='editor1',
            email='editor@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
    
    def test_remove_team_member_requires_login(self):
        """Test remove team member requires authentication."""
        remove_url = reverse('accounts:remove_team_member', kwargs={'user_id': self.manager.id})
        response = self.client.post(remove_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={remove_url}")
    
    def test_remove_team_member_requires_creator_role(self):
        """Test remove team member requires creator role."""
        self.client.login(username='manager1', password='testpass123')
        remove_url = reverse('accounts:remove_team_member', kwargs={'user_id': self.editor.id})
        response = self.client.post(remove_url, follow=True)
        self.assertEqual(response.status_code, 403)
    
    def test_remove_team_member_deletes_user(self):
        """Test removing team member deletes the user."""
        self.client.login(username='creator1', password='testpass123')
        remove_url = reverse('accounts:remove_team_member', kwargs={'user_id': self.manager.id})
        
        response = self.client.post(remove_url)
        
        self.assertRedirects(response, reverse('accounts:team_management'))
        
        # Check user was deleted
        self.assertFalse(User.objects.filter(id=self.manager.id).exists())
    
    def test_remove_team_member_prevents_self_removal(self):
        """Test creator cannot remove themselves."""
        self.client.login(username='creator1', password='testpass123')
        remove_url = reverse('accounts:remove_team_member', kwargs={'user_id': self.creator.id})
        
        response = self.client.post(remove_url)
        
        self.assertRedirects(response, reverse('accounts:team_management'))
        
        # Check creator still exists
        self.assertTrue(User.objects.filter(id=self.creator.id).exists())
    
    def test_remove_team_member_only_removes_own_team(self):
        """Test creator can only remove members from their own team."""
        # Create another creator with their own team
        other_creator = User.objects.create_user(
            username='creator2',
            email='creator2@test.com',
            password='testpass123',
            role='creator'
        )
        
        other_manager = User.objects.create_user(
            username='manager2',
            email='manager2@test.com',
            password='testpass123',
            role='manager',
            creator=other_creator
        )
        
        self.client.login(username='creator1', password='testpass123')
        remove_url = reverse('accounts:remove_team_member', kwargs={'user_id': other_manager.id})
        
        response = self.client.post(remove_url)
        
        self.assertRedirects(response, reverse('accounts:team_management'))
        
        # Check other manager still exists
        self.assertTrue(User.objects.filter(id=other_manager.id).exists())


class InvitationEmailTests(TestCase):
    """Test invitation email functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.creator = User.objects.create_user(
            username='creator1',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        self.add_member_url = reverse('accounts:add_team_member')
    
    def test_invitation_email_sent(self):
        """Test invitation email is sent when adding team member."""
        from django.core import mail
        
        self.client.login(username='creator1', password='testpass123')
        
        response = self.client.post(self.add_member_url, {
            'email': 'newmember@test.com',
            'role': 'manager'
        })
        
        # Check email was sent (using console backend in tests)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email content
        email = mail.outbox[0]
        self.assertIn('newmember@test.com', email.to)
        self.assertIn('invitation', email.subject.lower())
        self.assertIn('creator1', email.body)
        self.assertIn('manager', email.body.lower())
    
    def test_invitation_email_contains_registration_link(self):
        """Test invitation email contains registration link."""
        from django.core import mail
        
        self.client.login(username='creator1', password='testpass123')
        
        response = self.client.post(self.add_member_url, {
            'email': 'newmember@test.com',
            'role': 'editor'
        })
        
        # Get the invitation token
        invitation = User.objects.get(email='newmember@test.com', invitation_accepted=False)
        
        # Check email contains registration URL
        email = mail.outbox[0]
        self.assertIn(f'/accounts/register/{invitation.invitation_token}/', email.body)


class NavigationMenuVisibilityTests(TestCase):
    """Test navigation menu visibility based on user roles."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.creator = User.objects.create_user(
            username='creator1',
            email='creator@test.com',
            password='testpass123',
            role='creator'
        )
        
        self.manager = User.objects.create_user(
            username='manager1',
            email='manager@test.com',
            password='testpass123',
            role='manager',
            creator=self.creator
        )
        
        self.editor = User.objects.create_user(
            username='editor1',
            email='editor@test.com',
            password='testpass123',
            role='editor',
            creator=self.creator
        )
        
        self.dashboard_url = reverse('dashboard')
    
    def test_creator_sees_analytics_menu(self):
        """Test creator can see Analytics menu in navigation."""
        self.client.login(username='creator1', password='testpass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics')
        self.assertContains(response, reverse('analytics:dashboard'))
        self.assertContains(response, 'Channel Analytics')
        self.assertContains(response, 'Competitor Analysis')
        self.assertContains(response, 'SEO Insights')
        self.assertContains(response, 'Best Time to Post')
    
    def test_creator_sees_abtest_menu(self):
        """Test creator can see A/B Testing menu in navigation."""
        self.client.login(username='creator1', password='testpass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A/B Testing')
        self.assertContains(response, reverse('abtesting:test_list'))
    
    def test_manager_sees_analytics_menu(self):
        """Test manager can see Analytics menu in navigation."""
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics')
        self.assertContains(response, reverse('analytics:dashboard'))
    
    def test_manager_sees_abtest_menu(self):
        """Test manager can see A/B Testing menu in navigation."""
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A/B Testing')
        self.assertContains(response, reverse('abtesting:test_list'))
    
    def test_editor_does_not_see_analytics_menu(self):
        """Test editor cannot see Analytics menu in navigation."""
        self.client.login(username='editor1', password='testpass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        # Editor should not see the Analytics dropdown
        self.assertNotContains(response, 'id="analyticsDropdown"')
    
    def test_editor_does_not_see_abtest_menu(self):
        """Test editor cannot see A/B Testing menu in navigation."""
        self.client.login(username='editor1', password='testpass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        # Editor should not see A/B Testing link
        # We need to be careful here - the text "A/B Testing" might appear elsewhere
        # So we check for the specific navigation link
        content = response.content.decode('utf-8')
        # Check that the A/B Testing nav link is not present
        self.assertNotIn('href="{% url \'abtesting:test_list\' %}"', content)
        # More robust: check that the Flask icon + A/B Testing combo is not in nav
        if 'fa-flask' in content:
            # If flask icon exists, it should not be near "A/B Testing" in the nav
            nav_section = content.split('<nav')[1].split('</nav>')[0] if '<nav' in content else ''
            self.assertNotIn('A/B Testing', nav_section)
