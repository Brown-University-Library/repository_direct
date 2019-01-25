import json
import pathlib
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
import responses
from bdrcommon.identity import BDR_ACCESS
from .. import app_settings as settings
from ..views import _get_folders_param_from_collections
from workshop_common import test_data


CUR_DIR = pathlib.Path(__file__).parent


class AccessTest(TestCase):

    def test_landing(self):
        #test no Shib info, completely anonymous
        url = reverse('repo_direct:landing')
        r = self.client.get(url)
        self.assertRedirects(r, '%s?next=%s' % (reverse('login'), url))
        #test with Shib info, but no User in DB
        r = self.client.get(url, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, '%s?next=%s' % (reverse('login'), url))
        #test valid user
        User.objects.create_user(username='x@brown.edu')
        r = self.client.get(url, **{
                                'REMOTE_USER': 'x@brown.edu',
                                'Shibboleth-eppn': 'x@brown.edu'})
        self.assertContains(r, 'Please Enter a PID')


def responses_setup_for_display_view(object_type=None):
    responses.add(responses.GET, 'http://testserver/fedora/objects/test:123',
                  body=test_data.OBJECT_XML,
                  status=200,
                  content_type='text/xml'
                )
    if object_type == 'audio':
        datastreams_xml = test_data.MP3_DATASTREAMS_XML
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams/MP3',
                      body=test_data.DS_PROFILE_PATTERN.format(ds_id='MP3', ds_state='A'),
                      status=200,
                      content_type='text/xml'
                    )
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams/RELS-EXT/content',
                      body=test_data.RELS_EXT_XML.format(cmodel='audio'),
                      status=200,
                      content_type='text/xml'
                    )
    else:
        datastreams_xml = test_data.DATASTREAMS_XML
    responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams',
                  body=datastreams_xml,
                  status=200,
                  content_type='text/xml'
                )
    for ds_id in ['DC', 'RELS-EXT', 'rightsMetadata', 'MODS', 'irMetadata']:
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams/%s' % ds_id,
                      body=test_data.DS_PROFILE_PATTERN.format(ds_id=ds_id, ds_state='A'),
                      status=200,
                      content_type='text/xml'
                    )
    responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams/RELS-EXT/content',
                  body=test_data.RELS_EXT_XML.format(cmodel='pdf'),
                  status=200,
                  content_type='text/xml'
                )


class DisplayTest(TestCase):

    @responses.activate
    def test_get(self):
        responses_setup_for_display_view(object_type='audio')
        User.objects.create_user(username='x@brown.edu')
        url = reverse('repo_direct:display', kwargs={'pid': 'test:123'})
        r = self.client.get(url, **{
                                'REMOTE_USER': 'x@brown.edu',
                                'Shibboleth-eppn': 'x@brown.edu'})
        self.assertEqual(r.status_code, 200)
        self.assertInHTML('<a class="btn btn-primary btn-small" href="rightsMetadata/">View</a>', r.content.decode('utf8'))
        self.assertInHTML('<a class="btn btn-success btn-small" href="MODS/edit/">Edit</a>', r.content.decode('utf8'))
        self.assertContains(r, 'Update collections')
        self.assertContains(r, 'Extend embargo')
        self.assertContains(r, 'Create Streaming Derivative')

    @responses.activate
    def test_get_metadata_obj(self):
        responses_setup_for_display_view()
        User.objects.create_user(username='x@brown.edu')
        url = reverse('repo_direct:display', kwargs={'pid': 'test:123'})
        r = self.client.get(url, **{
                                'REMOTE_USER': 'x@brown.edu',
                                'Shibboleth-eppn': 'x@brown.edu'})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Create Streaming Derivative')

    @responses.activate
    def test_get_deleted_mods(self):
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123',
                      body=test_data.OBJECT_XML,
                      status=200,
                      content_type='text/xml'
                    )
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams',
                      body=test_data.DATASTREAMS_XML,
                      status=200,
                      content_type='text/xml'
                    )
        for ds_id in ['DC', 'RELS-EXT', 'rightsMetadata', 'irMetadata']:
            responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams/%s' % ds_id,
                          body=test_data.DS_PROFILE_PATTERN.format(ds_id=ds_id, ds_state='A'),
                          status=200,
                          content_type='text/xml'
                        )
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams/MODS',
                      body=test_data.DS_PROFILE_PATTERN.format(ds_id='MODS', ds_state='D'),
                      status=200,
                      content_type='text/xml'
                    )
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams/RELS-EXT/content',
                      body=test_data.RELS_EXT_XML.format(cmodel='pdf'),
                      status=200,
                      content_type='text/xml'
                    )
        User.objects.create_user(username='x@brown.edu')
        url = reverse('repo_direct:display', kwargs={'pid': 'test:123'})
        r = self.client.get(url, **{
                                'REMOTE_USER': 'x@brown.edu',
                                'Shibboleth-eppn': 'x@brown.edu'})
        self.assertEqual(r.status_code, 200)
        self.assertInHTML('<a class="btn btn-primary btn-small" href="rightsMetadata/">View</a>', r.content.decode('utf8'))
        self.assertInHTML('<td>MODS deleted</td>', r.content.decode('utf8'))


class EditItemCollectionTest(TestCase):

    def setUp(self):
        self.url = reverse('repo_direct:edit_item_collection', kwargs={'pid': 'test:123'})

    def test_auth(self):
        r = self.client.get(self.url, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, '%s?next=%s' % (reverse('login'), self.url.replace(':', '%3A')))

    @responses.activate
    def test_get(self):
        responses.add(responses.GET, 'http://testserver/storage/test:123/irMetadata/',
                      body=test_data.IR_METADATA_XML,
                      status=200,
                      content_type='text/xml'
                    )
        User.objects.create(username='someone@brown.edu', password='x')
        r = self.client.get(self.url, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Edit collections that test:123 belongs to')
        self.assertContains(r, 'Collection IDs')
        self.assertContains(r, 'value="1,2"')

    @responses.activate
    def test_post(self):
        responses_setup_for_display_view()
        responses.add(responses.PUT, 'http://testserver/api/private/items/',
                      body=json.dumps({}),
                      status=200,
                      content_type='application/json'
                    )
        User.objects.create(username='someone@brown.edu', password='x')
        data = {'collection_ids': '1, 2'}
        r = self.client.post(self.url, data, follow=True, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, reverse('repo_direct:display', kwargs={'pid': 'test:123'}))
        self.assertContains(r, 'Collection IDs for test:123 updated to &quot;1, 2&quot;')

    def test_get_folders_param_from_collections(self):
        folders_param = _get_folders_param_from_collections(['1', '2'])
        self.assertEqual(folders_param, '1#1+2#2')
        folders_param = _get_folders_param_from_collections(['1', ' 2'])
        self.assertEqual(folders_param, '1#1+2#2')
        folders_param = _get_folders_param_from_collections('')
        self.assertEqual(folders_param, '')
        folders_param = _get_folders_param_from_collections([])
        self.assertEqual(folders_param, '')
        folders_param = _get_folders_param_from_collections([''])
        self.assertEqual(folders_param, '')


class EmbargoTest(TestCase):

    def setUp(self):
        self.url = reverse('repo_direct:embargo', kwargs={'pid': 'test:123'})

    def test_auth(self):
        r = self.client.get(self.url, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, '%s?next=%s' % (reverse('login'), self.url.replace(':', '%3A')))

    def test_get(self):
        User.objects.create(username='someone@brown.edu', password='x')
        r = self.client.get(self.url, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertEqual(r.status_code, 200)

    @responses.activate
    def test_post(self):
        responses_setup_for_display_view()
        responses.add(responses.PUT, 'http://testserver/api/private/items/',
                      body=json.dumps({}),
                      status=200,
                      content_type='application/json'
                    )
        User.objects.create(username='someone@brown.edu', password='x')
        post_data = {'new_embargo_end_year': 2020}
        r = self.client.post(self.url, post_data, follow=True, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, reverse('repo_direct:display', kwargs={'pid': 'test:123'}))
        self.assertContains(r, '2020 added.')


class CreateStreamTest(TestCase):

    def setUp(self):
        self.url = reverse('repo_direct:create_stream', kwargs={'pid': 'test:123'})

    def test_auth(self):
        r = self.client.get(self.url, **{
                                'REMOTE_URL': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, '%s?next=%s' % (reverse('login'), self.url.replace(':', '%3A')))

    def test_get(self):
        User.objects.create(username='someone@brown.edu', password='x')
        r = self.client.get(self.url, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertEqual(r.status_code, 200)

    @responses.activate
    @patch('repo_direct_app.views._queue_stream_job')
    def test_post(self, mock_method):
        responses_setup_for_display_view()
        User.objects.create(username='someone@brown.edu', password='x')
        post_data = {'visibility': BDR_ACCESS.brown_only.name}
        r = self.client.post(self.url, post_data, follow=True, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, reverse('repo_direct:display', kwargs={'pid': 'test:123'}))
        self.assertContains(r, 'Queued streaming derivative job')
        mock_method.assert_called_once_with('test:123', visibility=BDR_ACCESS.brown_only.name)


class AddContentFileTest(TestCase):

    def setUp(self):
        self.url = reverse('repo_direct:add_content_file', kwargs={'pid': 'test:123'})

    def test_auth(self):
        r = self.client.get(self.url, **{
                                'REMOTE_URL': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, '%s?next=%s' % (reverse('login'), self.url.replace(':', '%3A')))

    def test_get(self):
        User.objects.create(username='someone@brown.edu', password='x')
        r = self.client.get(self.url, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertEqual(r.status_code, 200)

    @responses.activate
    def test_post_thumbnail(self):
        responses_setup_for_display_view()
        responses.add(responses.PUT, 'http://testserver/api/private/items/',
                      body=json.dumps({}),
                      status=200,
                      content_type='application/json'
                    )
        User.objects.create(username='someone@brown.edu', password='x')
        test_file_path = CUR_DIR / 'test_files' / 'thumb.jpg'
        with test_file_path.open(mode='rb') as f:
            post_data = {'content_file': f, 'is_thumbnail': 'on'}
            r = self.client.post(self.url, post_data, follow=True, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, reverse('repo_direct:display', kwargs={'pid': 'test:123'}))
        self.assertContains(r, 'Added thumbnail')

    @responses.activate
    def test_post_other_file(self):
        responses_setup_for_display_view()
        responses.add(responses.PUT, 'http://testserver/api/private/items/',
                      body=json.dumps({}),
                      status=200,
                      content_type='application/json'
                    )
        User.objects.create(username='someone@brown.edu', password='x')
        test_file_path = CUR_DIR / 'test_files' / 'image.png'
        with test_file_path.open(mode='rb') as f:
            post_data = {'content_file': f}
            r = self.client.post(self.url, post_data, follow=True, **{
                                'REMOTE_USER': 'someone@brown.edu',
                                'Shibboleth-eppn': 'someone@brown.edu'})
        self.assertRedirects(r, reverse('repo_direct:display', kwargs={'pid': 'test:123'}))
        self.assertContains(r, 'Added content')


class DatastreamEditorTest(TestCase):

    def setUp(self):
        User.objects.create_user(username='x@brown.edu')

    def _common_edit_test(self, reverse_name, dsid):
        r = self.client.get(
                reverse("repo_direct:{}".format(reverse_name),
                    kwargs={
                        'pid': 'test:123',
                        'dsid': dsid
                        }
                ),
                **{
                    'REMOTE_USER': 'x@brown.edu',
                    'Shibboleth-eppn': 'x@brown.edu'
                }
        )
        self.assertContains(r, "Edit test:123's {} datastream".format(dsid))

    @responses.activate
    def test_rights_xml_edit(self):
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams',
                  body=test_data.DATASTREAMS_XML,
                  status=200,
                  content_type='text/xml'
                )
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams/rightsMetadata/content',
                      body=test_data.RIGHTS_XML,
                      status=200,
                      content_type='text/xml'
                    )
        self._common_edit_test('xml-edit', 'rightsMetadata')

    @responses.activate
    def test_ir_metadata_xml_edit(self):
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams',
                  body=test_data.DATASTREAMS_XML,
                  status=200,
                  content_type='text/xml'
                )
        responses.add(responses.GET, 'http://testserver/fedora/objects/test:123/datastreams/irMetadata/content',
                      body=test_data.IR_METADATA_XML,
                      status=200,
                      content_type='text/xml'
                    )
        self._common_edit_test('xml-edit', 'irMetadata')

    def test_mods_xml_edit(self):
        url = reverse('repo_direct:xml-edit', kwargs={'pid': 'test:123', 'dsid': 'MODS'})
        r = self.client.head(url,
                **{
                    'REMOTE_USER': 'x@brown.edu',
                    'Shibboleth-eppn': 'x@brown.edu'
                }
            )
        self.assertEqual(r.status_code, 405)

