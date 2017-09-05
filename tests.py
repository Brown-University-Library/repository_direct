from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from . import app_settings as settings


def get_super_user_client():
    super_user = User.objects.create_superuser('superuser', 'test@example.com', 'pw')
    super_user_client = Client()
    super_user_client.login(username='superuser', password='pw')
    return super_user_client


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

