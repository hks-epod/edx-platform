"""
Tests for comprehensive theme static files storage classes.
"""
import ddt
import unittest
import re

from django.test import TestCase
from django.conf import settings

from openedx.core.djangoapps.theming.helpers import get_base_theme_dir
from openedx.core.djangoapps.theming.storage import CachedComprehensiveThemingStorage


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@ddt.ddt
class TestStorageLMS(TestCase):
    """
    Test comprehensive theming static files storage.
    """

    def setUp(self):
        super(TestStorageLMS, self).setUp()
        self.themes_dir = get_base_theme_dir()
        self.enabled_theme = "red-theme"
        self.system_dir = settings.REPO_ROOT / "lms"
        self.storage = CachedComprehensiveThemingStorage(location=self.themes_dir)

    @ddt.data(
        (True, "images/logo.png"),
        (True, "images/favicon.ico"),
        (False, "images/spinning.gif"),
    )
    @ddt.unpack
    def test_themed(self, is_themed, asset):
        """
        Verify storage returns True on themed assets
        """
        self.assertEqual(is_themed, self.storage.themed(asset, self.enabled_theme))

    @ddt.data(
        ("images/logo.png", ),
        ("images/favicon.ico", ),
    )
    @ddt.unpack
    def test_url(self, asset):
        """
        Verify storage returns correct url depending upon the enabled theme
        """
        asset_url = self.storage.url(asset, self.enabled_theme)
        # remove hash key from file url
        asset_url = re.sub(r"(\.\w+)(\.png|\.ico)$", r"\g<2>", asset_url)
        expected_url = self.storage.base_url + self.enabled_theme + "/" + asset

        self.assertEqual(asset_url, expected_url)

    @ddt.data(
        ("images/logo.png", ),
        ("images/favicon.ico", ),
    )
    @ddt.unpack
    def test_path(self, asset):
        """
        Verify storage returns correct file path depending upon the enabled theme
        """
        asset_url = self.storage.url(asset, self.enabled_theme)
        asset_url = asset_url.replace(self.storage.base_url, "")
        # remove hash key from file url
        asset_url = re.sub(r"(\.\w+)(\.png|\.ico)$", r"\g<2>", asset_url)
        returned_path = self.storage.path(asset_url)
        expected_path = self.themes_dir / self.enabled_theme / "lms/static/" / asset

        self.assertEqual(expected_path, returned_path)
