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
BDR_ADMIN = 'BROWN:DEPARTMENT:LIBRARY:REPOSITORY'
CREATE_STREAM_QUEUE = get_env_setting('CREATE_STREAM_QUEUE')

XML_DSIDS = [
    'MODS',
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

CONTENT_DSIDS = [

    #Content
    "content",

    #binarey metadata
    "META_MRC",

    #Image
    "thumbnail",
    "lowres",
    "highres",
    "highres_jp2",
    "JP2",
    "DIGITAL-NEGATIVE",
    "JPG", "jpg",
    "PNG", "png",
    "GIF", "gif",
    "MASTER_TIFF", "master_tiff",
    "MASTER",
    "MASTER_COLORBAR",
    "MASTER-COLORBAR",

    #Document
    "DOC",
    "DOCUMENTARY",
    "PDF", "pdf",
    "BW_PDF",
    "XLSX","xlsx",
    "TXT", "txt",
    "epub",

    #AUDIO
    "MP3", "mp3",
    "MP4", "mp4",

    #Video
    "M4V", "m4v",
    "MOV", "mov",

    #Data
    "CSV", "csv",

    #ARCHIVE
    "ZIP",
    "XTAR",
    "GZIP",
    "DJVU", "DJVU_XML",
    "torrent",
]
RIGHTS_ID = "rightsMetadata"
IR_ID = "irMetadata"
ALL_DSIDS = XML_DSIDS + CONTENT_DSIDS + [RIGHTS_ID , IR_ID]

