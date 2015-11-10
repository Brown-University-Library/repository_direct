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

