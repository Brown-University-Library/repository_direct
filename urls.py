from django.conf.urls import url, patterns
from eulfedora import views as eulviews
from . import app_settings as settings
from . import views



urlpatterns = patterns(
    '',
    url(
        regex= r'^$',
        view = views.landing,
        name = 'landing'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/$',
        view = views.display,
        name = 'display'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/reorder/$',
        view = views.reorder,
        name = 'reorder'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>({}))/edit/$'.format('|'.join(settings.XML_DSIDS)),
        view = views.xml_edit,
        name = 'xml-edit'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>(irMetadata))/edit/$',
        view = views.ir_edit,
        name = 'ir-edit'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>(rightsMetadata))/edit/$',
        view = views.rights_edit,
        name = 'rights-edit'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>({}))/edit/$'.format( '|'.join(settings.CONTENT_DSIDS)),
        view = views.file_edit,
        name = 'file-edit'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/AUDIT/$',
        view = eulviews.raw_audit_trail,
        name = 'audit'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>({}))/$'.format('|'.join(settings.ALL_DSIDS)),
        view = eulviews.raw_datastream,
        name = 'raw-datastream',
    ),

)
