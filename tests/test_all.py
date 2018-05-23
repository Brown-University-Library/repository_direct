import json
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
import responses
from .. import app_settings as settings
from ..forms import RightsMetadataEditForm
from workshop_common import test_data


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


class DisplayTest(TestCase):

    @responses.activate
    def test_get(self):
        responses.add(responses.GET, 'http://localhost/fedora/objects/test:123',
                      body=test_data.OBJECT_XML,
                      status=200,
                      content_type='text/xml'
                    )
        responses.add(responses.GET, 'http://localhost/fedora/objects/test:123/datastreams',
                      body=test_data.DATASTREAMS_XML,
                      status=200,
                      content_type='text/xml'
                    )
        for ds_id in ['DC', 'RELS-EXT', 'rightsMetadata', 'MODS']:
            responses.add(responses.GET, 'http://localhost/fedora/objects/test:123/datastreams/%s' % ds_id,
                          body=test_data.DS_PROFILE_PATTERN.format(ds_id=ds_id, ds_state='A'),
                          status=200,
                          content_type='text/xml'
                        )
        responses.add(responses.GET, 'http://localhost/fedora/objects/test:123/datastreams/RELS-EXT/content',
                      body=test_data.RELS_EXT_XML,
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
        self.assertInHTML('<a class="btn btn-success btn-small" href="MODS/edit/">Edit</a>', r.content.decode('utf8'))

    @responses.activate
    def test_get_deleted_mods(self):
        responses.add(responses.GET, 'http://localhost/fedora/objects/test:123',
                      body=test_data.OBJECT_XML,
                      status=200,
                      content_type='text/xml'
                    )
        responses.add(responses.GET, 'http://localhost/fedora/objects/test:123/datastreams',
                      body=test_data.DATASTREAMS_XML,
                      status=200,
                      content_type='text/xml'
                    )
        for ds_id in ['DC', 'RELS-EXT', 'rightsMetadata']:
            responses.add(responses.GET, 'http://localhost/fedora/objects/test:123/datastreams/%s' % ds_id,
                          body=test_data.DS_PROFILE_PATTERN.format(ds_id=ds_id, ds_state='A'),
                          status=200,
                          content_type='text/xml'
                        )
        responses.add(responses.GET, 'http://localhost/fedora/objects/test:123/datastreams/MODS',
                      body=test_data.DS_PROFILE_PATTERN.format(ds_id='MODS', ds_state='D'),
                      status=200,
                      content_type='text/xml'
                    )
        responses.add(responses.GET, 'http://localhost/fedora/objects/test:123/datastreams/RELS-EXT/content',
                      body=test_data.RELS_EXT_XML,
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


class RightsFormTest(TestCase):

    def setUp(self):
        User.objects.create_user(username='x@brown.edu')
        self.rights_edit_url = reverse('repo_direct:rights-edit',
                    kwargs={
                        'pid': 'test:1234',
                        'dsid': 'rightsMetadata'
                        }
                )

    def test_rights_editing_uses_rights_form(self):
        response = self.client.get(self.rights_edit_url,
                                **{
                                    'REMOTE_USER': 'x@brown.edu',
                                    'Shibboleth-eppn': 'x@brown.edu'})
        self.assertIsInstance(response.context['form'], RightsMetadataEditForm)

    def test_rights_editing_form_valid_data(self):
        data = { 'discover_and_read': ['BDR_PUBLIC','BROWN:COMMUNITY:ALL']}
        form = RightsMetadataEditForm(data)
        self.assertTrue(form.is_valid())

    def test_rights_editing_form_invalid_choice(self):
        data = { 'discover_and_read': ['not valid']}
        form = RightsMetadataEditForm(data)
        self.assertFalse(form.is_valid())
        self.assertEquals(
                form.errors['discover_and_read'],
                ['Select a valid choice. not valid is not one of the available choices.']
        )

    def test_rights_editing_form_invalid_string(self):
        data = { 'discover_and_read': 'invalid string'}
        form = RightsMetadataEditForm(data)
        self.assertFalse(form.is_valid())
        self.assertEquals(
                form.errors['discover_and_read'],
                [u"Enter a list of values."]
        )

    @responses.activate
    def test_rights_editing_post(self):
        responses.add(responses.PUT, 'http://testserver/api/private/items/',
                      body=json.dumps({}),
                      status=200,
                      content_type='application/json'
                    )
        data = { 'discover_and_read': ['BDR_PUBLIC','BROWN:COMMUNITY:ALL']}
        response = self.client.post(self.rights_edit_url, data,
                                **{
                                    'REMOTE_USER': 'x@brown.edu',
                                    'Shibboleth-eppn': 'x@brown.edu'})
        redirect_url = reverse('repo_direct:display', kwargs={'pid': 'test:1234'})
        self.assertRedirects(response, redirect_url, fetch_redirect_response=False)


class DatastreamEditorTest(TestCase):

    def setUp(self):
        User.objects.create_user(username='x@brown.edu')

    def _common_edit_test(self, reverse_name, dsid):
        r = self.client.get(
                reverse("repo_direct:{}".format(reverse_name),
                    kwargs={
                        'pid': 'test:1234',
                        'dsid': dsid
                        }
                ),
                **{
                    'REMOTE_USER': 'x@brown.edu',
                    'Shibboleth-eppn': 'x@brown.edu'
                }
        )
        self.assertContains(r, "Edit test:1234's {} datastream".format(dsid))

    def test_rights_edit(self):
        self._common_edit_test('rights-edit', 'rightsMetadata')

    @responses.activate
    def test_ir_metadata_edit(self):
        responses.add(responses.GET, 'https://localhost/api/collections/468/',
                      body=test_data.LIB_API_DATA,
                      status=200,
                      content_type='application/json'
                    )
        self._common_edit_test('ir-edit', 'irMetadata')


class RightsEditXmlTest(TestCase):

    @responses.activate
    def test_get(self):
        responses.add(responses.GET, 'http://localhost/fedora/objects/test:123/datastreams',
                      body=test_data.DATASTREAMS_XML,
                      status=200,
                      content_type='text/xml'
                    )
        responses.add(responses.GET, 'http://localhost/fedora/objects/test:123/datastreams/rightsMetadata/content',
                      body=test_data.RIGHTS_XML,
                      status=200,
                      content_type='text/xml'
                    )
        User.objects.create_user(username='x@brown.edu')
        url = reverse('repo_direct:rights-edit-xml',
                kwargs={'pid': 'test:123', 'dsid': 'rightsMetadata'})
        r = self.client.get(url,
                **{
                    'REMOTE_USER': 'x@brown.edu',
                    'Shibboleth-eppn': 'x@brown.edu'
                }
        )
        self.assertContains(r, "Edit test:123's rightsMetadata datastream")
        self.assertContains(r, 'Xml content')

