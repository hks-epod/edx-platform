"""
Platform related operations for Mobile APP
"""
import abc
from datetime import datetime
import re
from mobile_api.models import AppVersionConfig
from mobile_api.utils import parsed_version


class MobilePlatform(object):
    """
    MobilePlatform class creates an instance of platform based on user agent and supports platform
    related operations
    """
    __metaclass__ = abc.ABCMeta

    name = None
    version = None
    min_supported_version = None
    app_version_config = None

    @classmethod
    def get_min_supported_version(cls, version, app_version_config):
        """
        For any mobile app version being used; minimum supported version available is the immediate next configured
        version with a deadline.

        Parameters:
            version: mobile app version
            app_version_config: a dict with all available versions as key and their corresponding configuration as value

        Returns:
            for a given mobile app version; it returns the minimum supported version available from the
            configured versions
        """
        next_supported_version = None
        for supported_version_str, min_supported_version in app_version_config.iteritems():
            if min_supported_version.expire_at:
                app_version = parsed_version(version)
                supported_version = parsed_version(supported_version_str)
                if next_supported_version:
                    if (app_version < supported_version and
                       supported_version < parsed_version(next_supported_version.version)):
                        next_supported_version = min_supported_version
                elif app_version < supported_version:
                    next_supported_version = min_supported_version
        return next_supported_version

    @classmethod
    def get_instance(cls, user_agent):
        """
        It creates an instance of one of the supported mobile platforms (i.e. iOS, Android) by regex comparison
        of user-agent. The instance will contain:
            - name of the platform
            - version of the mobile app that made the request
            - min_supported_version for the platform
            - app_version_config: a dict with all available versions for platform as key and their corresponding
              configuration as value

        Parameters:
            user_agent: user_agent of mobile app

        Returns:
            instance of one of the supported mobile platforms (i.e. iOS, Android)
        """
        class Ios(MobilePlatform):
            """ iOS platform """
            USER_AGENT_REGEX = (r'\((?P<version>[0-9]+.[0-9]+.[0-9]+(.[0-9a-zA-Z]*)?); OS Version [0-9.]+ '
                                r'\(Build [0-9a-zA-Z]*\)\)')

            def __init__(self, version):
                self.name = AppVersionConfig.IOS
                self.version = version
                self.app_version_config = AppVersionConfig.get_all_versions(self.name)
                self.min_supported_version = MobilePlatform.get_min_supported_version(
                    self.version,
                    self.app_version_config
                )

            @classmethod
            def create_instance(cls, user_agent):
                """ Returns Ios platform instance if user_agent matches with USER_AGENT_REGEX for iOS """
                match = re.search(cls.USER_AGENT_REGEX, user_agent)
                if match:
                    version = match.group('version')
                    return cls(version)

        class Android(MobilePlatform):
            """ Android platform """
            USER_AGENT_REGEX = (r'Dalvik/[.0-9]+ \(Linux; U; Android [.0-9]+; (.*) Build/[0-9a-zA-Z]*\) '
                                r'(.*)/(?P<version>[0-9]+.[0-9]+.[0-9]+(.[0-9a-zA-Z]*)?)')

            def __init__(self, version):
                self.name = AppVersionConfig.ANDROID
                self.version = version
                self.app_version_config = AppVersionConfig.get_all_versions(self.name)
                self.min_supported_version = MobilePlatform.get_min_supported_version(
                    self.version,
                    self.app_version_config
                )

            @classmethod
            def create_instance(cls, user_agent):
                """ Returns Android platform instance if user_agent matches with USER_AGENT_REGEX for Android """
                match = re.search(cls.USER_AGENT_REGEX, user_agent)
                if match:
                    version = match.group('version')
                    return cls(version)

        # a list of all supported mobile platforms
        PLATFORM_CLASSES = [Ios, Android]  # pylint: disable=invalid-name
        for subclass in PLATFORM_CLASSES:
            instance = subclass.create_instance(user_agent)
            if instance:
                return instance

    def is_latest_version(self):
        """ Returns True if platform version is latest available version """
        if self.version in self.app_version_config:
            return self.app_version_config[self.version].is_latest
        return False

    def latest_version(self):
        """ iterates through all available versions and returns the version with latest flag configured as True """
        for version, config in self.app_version_config.iteritems():
            if config.is_latest:
                return version

    def is_outdated_version(self):
        """ Returns True if platform version < min supported version and timestamp < deadline to upgrade"""
        upgrade_date = self.upgrade_date()
        if upgrade_date and datetime.now() > upgrade_date.replace(tzinfo=None):
            return True
        return False

    def upgrade_date(self):
        """ returns deadline to upgrade to min supported version"""
        if self.version in self.app_version_config:
            user_version = self.app_version_config[self.version]
            if not self.min_supported_version:
                return user_version.expire_at
            else:
                if user_version.expire_at:
                    if self.version == self.min_supported_version:
                        return user_version.expire_at
                    elif datetime.now() >= user_version.expire_at.replace(tzinfo=None):
                        return self.min_supported_version.expire_at
                    else:
                        return user_version.expire_at
                else:
                    return self.min_supported_version.expire_at
        elif self.min_supported_version and self.version != self.min_supported_version.version:
            return self.min_supported_version.expire_at
