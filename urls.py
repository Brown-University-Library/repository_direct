from django.conf.urls import url
from eulfedora import views as eulviews
from . import app_settings as settings
from . import views


app_name = 'repo_direct'
urlpatterns = [
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
        regex= r'^(?P<pid>[^/]+)/edit/collection/$',
        view = views.edit_item_collection,
        name = 'edit_item_collection'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/edit/embargo/$',
        view = views.embargo,
        name = 'embargo'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/edit/create_stream/$',
        view = views.create_stream,
        name = 'create_stream'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>({}))/edit/$'.format('|'.join(settings.XML_DSIDS)),
        view = views.xml_edit,
        name = 'xml-edit'
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

]

