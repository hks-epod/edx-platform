"""
Middleware for Mobile APIs
"""
from django.http import HttpResponse
from mobile_api.mobile_platform import MobilePlatform
from mobile_api.utils import parsed_version
from openedx.core.lib.mobile_utils import is_request_from_mobile_app


class AppVersionUpgrade(object):
    """
    Middleware class to keep track of mobile application version being used
    """
    LATEST_VERSION_HEADER = "EDX-APP-LATEST-VERSION"
    UPGRADE_DEADLINE_HEADER = "EDX-APP-UPGRADE-DATE"

    def process_request(self, request):
        """
        raises HTTP Upgrade Require error if request is from mobile native app and
        user app version is no longer supported
        """
        if is_request_from_mobile_app(request):
            user_agent = request.META.get('HTTP_USER_AGENT')
            platform = MobilePlatform.get_instance(user_agent)
            if platform and platform.is_outdated_version():
                return HttpResponse(status=426)

    def process_response(self, _request, response):
        """
        If request is from mobile native app, then add headers to response;
        1. EDX-APP-LATEST-VERSION; if user app version < latest available version
        2. EDX-APP-UPGRADE-DATE; if user app version < min supported version and timestamp < deadline to upgrade
        """
        if is_request_from_mobile_app(_request):
            user_agent = _request.META.get('HTTP_USER_AGENT')
            platform = MobilePlatform.get_instance(user_agent)
            if platform:
                latest_version = platform.latest_version()
                if latest_version and parsed_version(latest_version) > parsed_version(platform.version):
                    response[self.LATEST_VERSION_HEADER] = latest_version
                if not platform.is_outdated_version():
                    upgrade_date = platform.upgrade_date()
                    if upgrade_date and platform.version != platform.min_supported_version.version:
                        response[self.UPGRADE_DEADLINE_HEADER] = upgrade_date
        return response
