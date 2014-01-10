from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

def get_app_setting(app_setting):
    """ Get the environment setting or return exception """
    try:
        return getattr(settings, app_setting)
    except AttributeError:
        error_msg = "Set the %s application setting" % app_setting
        raise ImproperlyConfigured(error_msg)

FOLDER_API_PUBLIC = get_app_setting("FOLDER_API_PUBLIC")
LIBRARY_PARENT_FOLDER_ID = get_app_setting("LIBRARY_PARENT_FOLDER_ID")
DEFAULT_RIGHTS_CHOICES = get_app_setting("DEFAULT_RIGHTS_CHOICES")
