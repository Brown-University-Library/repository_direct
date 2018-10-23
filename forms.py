from django import forms
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput
from django.contrib.admin.widgets import AdminFileWidget

import requests
from eulxml.xmlmap import load_xmlobject_from_string
from bdrxml import irMetadata
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django_ace import AceWidget

from . import app_settings as settings


class FileReplacementForm( forms.Form ):
    replacement_file = forms.FileField(label="File", widget=AdminFileWidget)


class CommonFormHelperMixin(object):
    @property
    def helper(self):
        if not hasattr(self, '_helper'):
            self._helper = FormHelper()
            self._helper.form_class = 'col-md-6 col-md-offset-3'
            self._helper.add_input(Submit('submit', 'Save'))
        return self._helper

class EditXMLForm( forms.Form , CommonFormHelperMixin):
    xml_content = forms.CharField(widget=AceWidget(mode='xml', width="100%", height="500px"))



class RepoLandingForm(forms.Form):
    pid = forms.CharField(error_messages={'required': 'Please enter a pid'})


class ItemCollectionsForm(forms.Form):

    collection_ids = forms.CharField(required=False, help_text='list collection IDs separated by "," - eg. "1,2"')

    @staticmethod
    def from_storage_data(pid):
        r = requests.get(f'{settings.STORAGE_BASE_URL}{pid}/irMetadata/')
        if not r.ok:
            raise Exception(f'{r.status_code} - {r.text}')
        ir_obj = load_xmlobject_from_string(r.content, irMetadata.IR)
        return ItemCollectionsForm({'collection_ids': ','.join(ir_obj.collection_list)})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collection_ids'].label = 'Collection IDs'
        self.helper = FormHelper()
        self.helper.form_class = 'col-md-6 col-md-offset-3'
        self.helper.add_input(Submit('submit', 'Save Collection IDs'))


class EmbargoForm(forms.Form):

    new_embargo_end_year = forms.IntegerField(help_text='API will handle setting the embargoed status, but won\'t update any access controls.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'col-md-6 col-md-offset-3'
        self.helper.add_input(Submit('submit', 'Add Embargo Year'))


class CreateStreamForm(forms.Form):

    visibility = forms.ChoiceField(choices=( ('brown', 'Brown Only'), ('public', 'Public') ),
            help_text='If you need other visibility options, please contact the BDR team.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'col-md-6 col-md-offset-3'
        self.helper.add_input(Submit('submit', 'Create Stream'))


class ReorderForm(forms.Form):
    child_pids_ordered_list = forms.CharField(required=True, widget=HiddenInput)

