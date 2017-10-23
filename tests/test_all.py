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


class RightsFormTest(TestCase):

    def setUp(self):
        User.objects.create_user(username='x@brown.edu')
        self.rights_edit_url = reverse("repo_direct:{}".format('rights-edit'),
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

    def test_rights_editing_form_post_valid_data(self):
        data = { 'discover_and_read': ['BDR_PUBLIC','BROWN:COMMUNITY:ALL']}
        form = RightsMetadataEditForm(data)
        self.assertTrue(form.is_valid())

    def test_rights_editing_form_post_invalid_choice(self):
        data = { 'discover_and_read': ['not valid']}
        form = RightsMetadataEditForm(data)
        self.assertFalse(form.is_valid())
        self.assertEquals(
                form.errors['discover_and_read'],
                [u"Select a valid choice. not valid is not one of the available choices."]
        )

    def test_rights_editing_form_post_invalid_string(self):
        data = { 'discover_and_read': 'invalid string'}
        form = RightsMetadataEditForm(data)
        self.assertFalse(form.is_valid())
        self.assertEquals(
                form.errors['discover_and_read'],
                [u"Enter a list of values."]
        )


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

