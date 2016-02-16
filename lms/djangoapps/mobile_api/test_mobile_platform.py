"""
tests for platform against mobile app request
"""
from datetime import datetime
import ddt
from django.test import TestCase
from pytz import UTC
from mobile_api.mobile_platform import MobilePlatform
from mobile_api.models import AppVersionConfig


@ddt.ddt
class TestMobilePlatform(TestCase):
    """ Tests for platform against mobile app request """
    def setUp(self):
        super(TestMobilePlatform, self).setUp()
        self.set_app_version_config()

    def set_app_version_config(self):
        """ creates configuration data for platform versions """
        AppVersionConfig(platform="ios", version="1.1.1", expire_at=None, is_latest=False).save()
        AppVersionConfig(
            platform="ios",
            version="2.2.2",
            expire_at=datetime(2014, 01, 01).replace(tzinfo=UTC),
            is_latest=False
        ).save()
        AppVersionConfig(
            platform="ios",
            version="4.4.4",
            expire_at=datetime(9000, 01, 01).replace(tzinfo=UTC),
            is_latest=False
        ).save()
        AppVersionConfig(platform="ios", version="6.6.6", expire_at=None, is_latest=True).save()

        AppVersionConfig(platform="android", version="1.1.1", expire_at=None, is_latest=False).save()
        AppVersionConfig(
            platform="android",
            version="2.2.2",
            expire_at=datetime(2014, 01, 01).replace(tzinfo=UTC),
            is_latest=False
        ).save()
        AppVersionConfig(
            platform="android",
            version="4.4.4",
            expire_at=datetime(9000, 01, 01).replace(tzinfo=UTC),
            is_latest=False
        ).save()
        AppVersionConfig(platform="android", version="6.6.6", expire_at=None, is_latest=True).save()

    @ddt.data(
        ("edX/org.edx.mobile (1.1.1; OS Version 9.2 (Build 13C75))", AppVersionConfig.IOS, "1.1.1", "2.2.2"),
        ("edX/org.edx.mobile (2.2.2; OS Version 9.2 (Build 13C75))", AppVersionConfig.IOS, "2.2.2", "4.4.4"),
        ("edX/org.edx.mobile (3.3.3; OS Version 9.2 (Build 13C75))", AppVersionConfig.IOS, "3.3.3", "4.4.4"),
        (
            "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/1.1.1",
            AppVersionConfig.ANDROID,
            "1.1.1",
            "2.2.2"
        ),
        (
            "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/2.2.2",
            AppVersionConfig.ANDROID,
            "2.2.2",
            "4.4.4"
        ),
        (
            "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/3.3.3",
            AppVersionConfig.ANDROID,
            "3.3.3",
            "4.4.4"
        ),
    )
    @ddt.unpack
    def test_platform_instance(self, user_agent, platform_name, version, min_supported_version):
        platform = MobilePlatform.get_instance(user_agent)
        self.assertEqual(platform_name, platform.name)
        self.assertEqual(version, platform.version)
        self.assertEqual(min_supported_version, platform.min_supported_version.version)

    @ddt.data(
        ("edX/org.edx.mobile (1.0.2; OS Version 9.2 (Build 13C75))", False),
        ("edX/org.edx.mobile (2.2.2; OS Version 9.2 (Build 13C75))", False),
        ("edX/org.edx.mobile (6.6.6; OS Version 9.2 (Build 13C75))", True),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/1.0.2", False),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/2.2.2", False),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/6.6.6", True),
    )
    @ddt.unpack
    def test_is_latest_version(self, user_agent, result):
        platform = MobilePlatform.get_instance(user_agent)
        self.assertEqual(result, platform.is_latest_version())

    @ddt.data(
        ("edX/org.edx.mobile (1.0.1; OS Version 9.2 (Build 13C75))", True),
        ("edX/org.edx.mobile (1.1.1; OS Version 9.2 (Build 13C75))", True),
        ("edX/org.edx.mobile (2.0.5; OS Version 9.2 (Build 13C75))", True),
        ("edX/org.edx.mobile (4.4.4; OS Version 9.2 (Build 13C75))", False),
        ("edX/org.edx.mobile (5.5.5; OS Version 9.2 (Build 13C75))", False),
        ("edX/org.edx.mobile (6.6.6; OS Version 9.2 (Build 13C75))", False),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/1.0.1", True),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/1.1.1", True),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/2.0.5", True),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/4.4.4", False),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/5.5.5", False),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/6.6.6", False),
    )
    @ddt.unpack
    def test_is_outdated_version(self, user_agent, result):
        platform = MobilePlatform.get_instance(user_agent)
        self.assertEqual(result, platform.is_outdated_version())

    @ddt.data(
        ("edX/org.edx.mobile (1.0.2; OS Version 9.2 (Build 13C75))", datetime(2014, 01, 01).replace(tzinfo=UTC)),
        ("edX/org.edx.mobile (2.2.2; OS Version 9.2 (Build 13C75))", datetime(9000, 01, 01).replace(tzinfo=UTC)),
        ("edX/org.edx.mobile (3.3.3; OS Version 9.2 (Build 13C75))", datetime(9000, 01, 01).replace(tzinfo=UTC)),
        ("edX/org.edx.mobile (4.4.4; OS Version 9.2 (Build 13C75))", datetime(9000, 01, 01).replace(tzinfo=UTC)),
        ("edX/org.edx.mobile (6.6.6; OS Version 9.2 (Build 13C75))", None),
        ("edX/org.edx.mobile (7.7.7; OS Version 9.2 (Build 13C75))", None),
        (
            "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/1.0.2",
            datetime(2014, 01, 01).replace(tzinfo=UTC)
        ),
        (
            "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/2.2.2",
            datetime(9000, 01, 01).replace(tzinfo=UTC)
        ),
        (
            "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/3.3.3",
            datetime(9000, 01, 01).replace(tzinfo=UTC)
        ),
        (
            "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/4.4.4",
            datetime(9000, 01, 01).replace(tzinfo=UTC)
        ),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/6.6.6", None),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/7.7.7", None),
    )
    @ddt.unpack
    def test_upgrade_date(self, user_agent, upgrade_date):
        platform = MobilePlatform.get_instance(user_agent)
        self.assertEqual(upgrade_date, platform.upgrade_date())
