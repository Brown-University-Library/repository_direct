from django.conf.urls import url, patterns
from eulfedora.views import raw_datastream, raw_audit_trail


urlpatterns = patterns(
    'repo_direct_app.views',
    url('^$', 'landing', name='landing'),
    #url('^upload/$', 'upload', name='upload'),
    url(r'^(?P<pid>[^/]+)/$', 'display', name='display'),
    url(r'^(?P<pid>[^/]+)/(?P<dsid>(MODS|RELS-EXT|DC|METS|RELS-INT))/edit/$', 'xml_edit', name='xml-edit'),
    url(r'^(?P<pid>[^/]+)/(?P<dsid>(irMetadata))/edit/$', 'ir_edit', name='ir-edit'),
    url(r'^(?P<pid>[^/]+)/(?P<dsid>(rightsMetadata))/edit/$', 'rights_edit', name='rights-edit'),
    url(r'^(?P<pid>[^/]+)/(?P<dsid>(tiff|jpg|JP2|PDF|content))/edit/$', 'file_edit', name='file-edit'),
)
urlpatterns += patterns(
    '',
    url(r'^(?P<pid>[^/]+)/AUDIT/$', raw_audit_trail),
    url(r'^(?P<pid>[^/]+)/(?P<dsid>(MODS|RELS-EXT|DC|METS|RELS-INT))/$', raw_datastream),
    url(r'^(?P<pid>[^/]+)/(?P<dsid>(irMetadata|rightsMetadata))/$', raw_datastream),
    url(r'^(?P<pid>[^/]+)/(?P<dsid>(tiff|jpg|JP2|PDF|content))/$', raw_datastream),

)
