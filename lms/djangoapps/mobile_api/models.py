"""
ConfigurationModel for the mobile_api djangoapp.
"""
from django.db.models.fields import TextField, DateTimeField, CharField, BooleanField
from config_models.models import ConfigurationModel, cache


class MobileApiConfig(ConfigurationModel):
    """
    Configuration for the video upload feature.

    The order in which the comma-separated list of names of profiles are given
    is in priority order.
    """
    video_profiles = TextField(
        blank=True,
        help_text="A comma-separated list of names of profiles to include for videos returned from the mobile API."
    )

    @classmethod
    def get_video_profiles(cls):
        """
        Get the list of profiles in priority order when requesting from VAL
        """
        return [profile.strip() for profile in cls.current().video_profiles.split(",") if profile]


class AppVersionConfig(ConfigurationModel):  # pylint: disable=model-missing-unicode
    """
    Configuration for mobile app versions available.
    """
    IOS = "ios"
    ANDROID = "android"
    PLATFORM = (
        (IOS, "iOS"),
        (ANDROID, "Android"),

    )
    KEY_FIELDS = ('platform', 'version')  # combination of mobile platform and version is unique
    platform = CharField(max_length=50, choices=PLATFORM, blank=False)
    version = CharField(max_length=50, blank=False)
    expire_at = DateTimeField(null=True, blank=True, verbose_name="Last Supported Date")
    is_latest = BooleanField(default=False)

    @classmethod
    def cache_key_name(cls, *args):
        """Return the name of the key to use to cache all versions configuration against platform"""
        return u'configuration/{}/current/{}'.format(cls.__name__, u','.join(unicode(arg) for arg in args))

    @classmethod
    def get_all_versions(cls, platform):
        """
        it returns and caches a dict with all available versions for platform as key and
        their corresponding configuration as value
        """
        cached = cache.get(cls.cache_key_name(platform))
        if cached is not None:
            return cached

        try:
            platform_versions = cls.objects.filter(platform=platform).order_by('-change_date')
        except IndexError:
            return None
        version_dict = {}
        for app_version in platform_versions:
            if app_version.version not in version_dict:
                version_dict[app_version.version] = app_version

        cache.set(
            cls.cache_key_name(platform),
            version_dict,
            ConfigurationModel.cache_timeout)
        return version_dict

    def save(self, *args, **kwargs):
        """
        clear the cached value when saving a new configuration entry
        if new entry has is_latest flag as True; mark any existing latest versions as False
        """
        # Always create a new entry, instead of updating an existing model
        self.pk = None  # pylint: disable=invalid-name
        if self.is_latest:
            latest_versions = AppVersionConfig.objects.filter(platform=self.platform, is_latest=True)
            if latest_versions:
                for version in latest_versions:
                    if version.is_latest:
                        version.is_latest = False
                        version.save()
        super(AppVersionConfig, self).save(*args, **kwargs)
        cache.delete(AppVersionConfig.cache_key_name(self.platform))
