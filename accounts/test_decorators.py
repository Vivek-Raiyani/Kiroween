"""
Tests for role-based access control decorators.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from .decorators import analytics_required, abtest_required

User = get_user_model()


class AnalyticsRequiredDecoratorTests(TestCase):
    """Test analytics_required decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
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
        
        # Create a simple view for testing
        @analytics_required
        def test_view(request):
            return HttpResponse("Success")
        
        self.test_view = test_view
    
    def _add_middleware_to_request(self, request):
        """Add required middleware to request."""
        # Add session
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        return request
    
    def test_creator_has_access(self):
        """Test creator can access analytics."""
        request = self.factory.get('/analytics/')
        request.user = self.creator
        request = self._add_middleware_to_request(request)
        
        response = self.test_view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
    
    def test_manager_has_access(self):
        """Test manager can access analytics."""
        request = self.factory.get('/analytics/')
        request.user = self.manager
        request = self._add_middleware_to_request(request)
        
        response = self.test_view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
    
    def test_editor_denied_access(self):
        """Test editor is denied access to analytics."""
        request = self.factory.get('/analytics/')
        request.user = self.editor
        request = self._add_middleware_to_request(request)
        
        response = self.test_view(request)
        
        # Should redirect to permission denied
        self.assertEqual(response.status_code, 302)
        self.assertIn('accounts/permission-denied', response.url)


class ABTestRequiredDecoratorTests(TestCase):
    """Test abtest_required decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
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
        
        # Create a simple view for testing
        @abtest_required
        def test_view(request):
            return HttpResponse("Success")
        
        self.test_view = test_view
    
    def _add_middleware_to_request(self, request):
        """Add required middleware to request."""
        # Add session
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        return request
    
    def test_creator_has_access(self):
        """Test creator can access A/B testing."""
        request = self.factory.get('/abtesting/')
        request.user = self.creator
        request = self._add_middleware_to_request(request)
        
        response = self.test_view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
    
    def test_manager_has_access(self):
        """Test manager can access A/B testing."""
        request = self.factory.get('/abtesting/')
        request.user = self.manager
        request = self._add_middleware_to_request(request)
        
        response = self.test_view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
    
    def test_editor_denied_access(self):
        """Test editor is denied access to A/B testing."""
        request = self.factory.get('/abtesting/')
        request.user = self.editor
        request = self._add_middleware_to_request(request)
        
        response = self.test_view(request)
        
        # Should redirect to permission denied
        self.assertEqual(response.status_code, 302)
        self.assertIn('accounts/permission-denied', response.url)
