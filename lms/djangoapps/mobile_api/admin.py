"""
Django admin dashboard configuration for LMS XBlock infrastructure.
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from mobile_api.models import MobileApiConfig, AppVersionConfig

admin.site.register(MobileApiConfig, ConfigurationModelAdmin)
admin.site.register(AppVersionConfig, KeyedConfigurationModelAdmin)
