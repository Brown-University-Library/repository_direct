from django.conf.urls import url, patterns
from eulfedora.views import raw_datastream, raw_audit_trail
from eulfedora import views as eulviews
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
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>(MODS|RELS-EXT|DC|METS|RELS-INT))/edit/$',
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
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>(tiff|jpg|JP2|PDF|content))/edit/$',
        view = views.file_edit,
        name = 'file-edit'
    ),
)
urlpatterns += patterns(
    '',
    url(
        regex= r'^(?P<pid>[^/]+)/AUDIT/$',
        view = eulviews.raw_audit_trail
        name = 'audit'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>(MODS|RELS-EXT|DC|METS|RELS-INT))/$',
        view = eulviews.raw_datastream,
        name = 'raw-datastream'
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>(irMetadata|rightsMetadata))/$',
        view = eulviews.raw_datastream
    ),
    url(
        regex= r'^(?P<pid>[^/]+)/(?P<dsid>(tiff|jpg|JP2|PDF|content))/$',
        view = eulviews.raw_datastream
    ),

)
