from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from eulfedora import views as eulviews
from . import app_settings as settings
from . import views


app_name = 'repo_direct'
urlpatterns = [
    url(
        regex= r'^$',
        view = login_required(views.landing),
        name = 'landing'
    ),
    url(
        regex= r'^new/$',
        view = login_required(views.new_object),
        name = 'new_object'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/$',
        view = login_required(views.display),
        name = 'display'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/reorder/$',
        view = login_required(views.reorder),
        name = 'reorder'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/edit/collection/$',
        view = login_required(views.edit_item_collection),
        name = 'edit_item_collection'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/edit/embargo/$',
        view = login_required(views.embargo),
        name = 'embargo'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/edit/create_stream/$',
        view = login_required(views.create_stream),
        name = 'create_stream'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/edit/add_content_file/$',
        view = login_required(views.add_content_file),
        name = 'add_content_file'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>({}))/edit/$'.format('|'.join(settings.XML_DSIDS)),
        view = login_required(views.xml_edit),
        name = 'xml-edit'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>[\w-]+)/edit/$',
        view = login_required(views.file_edit),
        name = 'file-edit'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/AUDIT/$',
        view = login_required(eulviews.raw_audit_trail),
        name = 'audit'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>[\w-]+)/$',
        view = login_required(eulviews.raw_datastream),
        name = 'raw-datastream',
    ),

]

