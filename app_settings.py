import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_app_setting(app_setting):
    """ Get the environment setting or return exception """
    try:
        return getattr(settings, app_setting)
    except AttributeError:
        error_msg = "Set the %s application setting" % app_setting
        raise ImproperlyConfigured(error_msg)


def get_env_setting(setting):
    """ Get the environment setting or return exception """
    try:
        return os.environ[setting]
    except KeyError:
        error_msg = "Set the %s env variable" % setting
        raise ImproperlyConfigured(error_msg)


BDR_BASE = get_app_setting("BDR_BASE")
REORDER_URL = '%s/api/private/reorder/' % BDR_BASE
THUMBNAIL_BASE_URL = '%s/viewers/image/thumbnail' % BDR_BASE
STORAGE_BASE_URL = f'{BDR_BASE}/storage/'
STUDIO_ITEM_URL = '%s/studio/item' % BDR_BASE
ITEM_POST_URL = get_app_setting("ITEM_POST_URL")
FOLDER_API_PUBLIC = get_app_setting("FOLDER_API_PUBLIC")
LIBRARY_PARENT_FOLDER_ID = get_app_setting("LIBRARY_PARENT_FOLDER_ID")
DEFAULT_RIGHTS_CHOICES = get_app_setting("DEFAULT_RIGHTS_CHOICES")

XML_DSIDS = [
    'MODS',
    'rightsMetadata',
    'irMetadata',
    'RELS-EXT',
    'RELS-INT',
    'METS',
    'DC',
    "IA_DC",
    "DWC",
    "XML", "xml",
    "MARC_XML",
    "METASOURCE_XML", "META_XML",
    "SCANDATA_XML",
    "archiveMETS",
]

