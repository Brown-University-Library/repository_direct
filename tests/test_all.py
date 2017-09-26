from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from .. import app_settings as settings
import unittest
from ..forms import RightsMetadataEditForm


def get_super_user_client():
    super_user = User.objects.create_superuser('superuser', 'test@example.com', 'pw')
    super_user_client = Client()
    super_user_client.login(username='superuser', password='pw')
    return super_user_client


class RightsFormTest(TestCase):
    def setUp(self):
        self.client = get_super_user_client()
        self.rights_edit_url = reverse("repo_direct:{}".format('rights-edit'),
                    kwargs={
                        'pid': 'test:1234',
                        'dsid': 'rightsMetadata'
                        }
                )

    def test_rights_editing_uses_rights_form(self):
        response = self.client.get(self.rights_edit_url)
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

    def _common_edit_test(self, reverse_name, dsid):
        client = get_super_user_client()
        r = client.get(
                reverse("repo_direct:{}".format(reverse_name),
                    kwargs={
                        'pid': 'test:1234',
                        'dsid': dsid
                        }
                )
        )
        self.assertContains(r, "Edit test:1234's {} datastream".format(dsid))

    def test_rights_edit(self):
        self._common_edit_test('rights-edit', 'rightsMetadata')

    def test_ir_metadata_edit(self):
        self._common_edit_test('ir-edit', 'irMetadata')

