"""
Provides unit tests for SSL based authentication portions
of the external_auth app.
"""
import copy
import unittest

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.client import RequestFactory
from django.test.utils import override_settings
from edxmako.middleware import MakoMiddleware
from external_auth.models import ExternalAuthMap
import external_auth.views
from mock import Mock

from student.models import CourseEnrollment
from student.roles import CourseStaffRole
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

FEATURES_WITH_SSL_AUTH = settings.FEATURES.copy()
FEATURES_WITH_SSL_AUTH['AUTH_USE_CERTIFICATES'] = True
FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP = FEATURES_WITH_SSL_AUTH.copy()
FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP['AUTH_USE_CERTIFICATES_IMMEDIATE_SIGNUP'] = True
FEATURES_WITH_SSL_AUTH_AUTO_ACTIVATE = FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP.copy()
FEATURES_WITH_SSL_AUTH_AUTO_ACTIVATE['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH'] = True
FEATURES_WITHOUT_SSL_AUTH = settings.FEATURES.copy()
FEATURES_WITHOUT_SSL_AUTH['AUTH_USE_CERTIFICATES'] = False
CACHES_ENABLE_GENERAL = copy.deepcopy(settings.CACHES)
CACHES_ENABLE_GENERAL['general']['BACKEND'] = 'django.core.cache.backends.locmem.LocMemCache'


@override_settings(FEATURES=FEATURES_WITH_SSL_AUTH)
@override_settings(CACHES=CACHES_ENABLE_GENERAL)
class SSLClientTest(ModuleStoreTestCase):
    """
    Tests SSL Authentication code sections of external_auth
    """

    AUTH_DN = '/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}'
    USER_NAME = 'test_user_ssl'
    USER_EMAIL = 'test_user_ssl@EDX.ORG'
    MOCK_URL = '/'

    def _create_ssl_request(self, url):
        """Creates a basic request for SSL use."""
        request = self.factory.get(url)
        request.META['SSL_CLIENT_S_DN'] = self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        MakoMiddleware().process_request(request)
        return request

    def _create_normal_request(self, url):
        """Creates sessioned request without SSL headers"""
        request = self.factory.get(url)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        MakoMiddleware().process_request(request)
        return request

    def setUp(self):
        """Setup test case by adding primary user."""
        super(SSLClientTest, self).setUp()
        self.client = Client()
        self.factory = RequestFactory()
        self.mock = Mock()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITHOUT_SSL_AUTH)
    def test_ssl_decorator_no_certs(self):
        """Make sure no external auth happens without SSL enabled"""

        dec_mock = external_auth.views.ssl_login_shortcut(self.mock)
        request = self._create_normal_request(self.MOCK_URL)
        request.user = AnonymousUser()
        # Call decorated mock function to make sure it passes
        # the call through without hitting the external_auth functions and
        # thereby creating an external auth map object.
        dec_mock(request)
        self.assertTrue(self.mock.called)
        self.assertEqual(0, len(ExternalAuthMap.objects.all()))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_ssl_login_decorator(self):
        """Create mock function to test ssl login decorator"""

        dec_mock = external_auth.views.ssl_login_shortcut(self.mock)

        # Test that anonymous without cert doesn't create authmap
        request = self._create_normal_request(self.MOCK_URL)
        dec_mock(request)
        self.assertTrue(self.mock.called)
        self.assertEqual(0, len(ExternalAuthMap.objects.all()))

        # Test logged in user gets called
        self.mock.reset_mock()
        request = self._create_ssl_request(self.MOCK_URL)
        request.user = UserFactory()
        dec_mock(request)
        self.assertTrue(self.mock.called)
