"""
Static file finders for Django.
https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-STATICFILES_FINDERS
Yes, this interface is private and undocumented, but we need to access it anyway.

In order to deploy Open edX in production, it's important to be able to collect
and process static assets: images, CSS, JS, fonts, etc. Django's collectstatic
system is the accepted way to do that in Django-based projects, but that system
doesn't handle every kind of collection and processing that web developers need.
Other open source projects like `Django-Pipeline`_ and `Django-Require`_ hook
into Django's collectstatic system to provide features like minification,
compression, Sass pre-processing, and require.js optimization for assets before
they are pushed to production. To make sure that themed assets are collected
and served by the system (in addition to core assets), we need to extend this
interface, as well.

.. _Django-Pipeline: http://django-pipeline.readthedocs.org/
.. _Django-Require: https://github.com/etianen/django-require
"""
from path import Path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles import utils
from django.contrib.staticfiles.finders import BaseFinder
from openedx.core.djangoapps.theming.helpers import (
    get_base_theme_dir
)
from openedx.core.djangoapps.theming.storage import CachedComprehensiveThemingStorage


class ComprehensiveThemeFinder(BaseFinder):
    """
    A static files finder that searches the active comprehensive theme
    for static files. If the ``COMPREHENSIVE_THEME_DIR`` setting is unset,
    or the ``COMPREHENSIVE_THEME_DIR`` does not exist on the file system,
    this finder will never find any files.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize finder with comprehensive theming storage if we have
        a valid COMPREHENSIVE_THEME_DIR setting.
        """
        super(ComprehensiveThemeFinder, self).__init__(*args, **kwargs)

        themes_dir = get_base_theme_dir()
        if not themes_dir:
            self.storage = None
            return

        if not isinstance(themes_dir, basestring):
            raise ImproperlyConfigured("Your COMPREHENSIVE_THEME_DIR setting must be a string")

        self.storage = CachedComprehensiveThemingStorage(location=themes_dir)

    def find(self, path, all=False):  # pylint: disable=redefined-builtin
        """
        Looks for files in the default file storage, if it's local.
        """
        if not self.storage:
            return []

        if self.storage.exists(path):
            match = self.storage.path(path)
            if all:
                match = [match]
            return match

        return []

    def list(self, ignore_patterns):
        """
        List all files of the storage.
        """
        if self.storage and self.storage.exists(''):
            for path in utils.get_files(self.storage, ignore_patterns):
                yield path, self.storage
