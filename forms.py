"""Forms for repo application"""
from django import forms
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput
from django.contrib.admin.widgets import AdminFileWidget

import requests
from eulxml.xmlmap import load_xmlobject_from_string
from bdrxml.rights import RightsBuilder
from bdrxml import irMetadata
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django_ace import AceWidget
from django_select2 import forms as s2forms

from . import app_settings as settings

RIGHTS_CHOICES = zip(
        settings.DEFAULT_RIGHTS_CHOICES,
        settings.DEFAULT_RIGHTS_CHOICES
    )


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


class RightsSelectWidgetMixin(object):
    def build_attrs(self, *args, **kwargs):
        self.attrs.setdefault('data-minimum-input-length', 0)
        return super(RightsSelectWidgetMixin, self).build_attrs(*args, **kwargs)


class RightsSelectWidget(RightsSelectWidgetMixin, s2forms.Select2TagWidget):
    pass


class RightsMetadataEditForm(forms.Form, CommonFormHelperMixin):
    discover_and_read = forms.MultipleChoiceField(
            required=False,
            widget=RightsSelectWidget,
            choices = RIGHTS_CHOICES,
    )
    discover_only = forms.MultipleChoiceField(
            required=False,
            widget=RightsSelectWidget,
            choices = RIGHTS_CHOICES,
    )
    read_only = forms.MultipleChoiceField(
            required=False,
            widget=RightsSelectWidget,
            choices = RIGHTS_CHOICES,
    )
    edit_rights = forms.MultipleChoiceField(
            required=False,
            widget=RightsSelectWidget,
            choices = RIGHTS_CHOICES,
    )
    owners = forms.MultipleChoiceField(
            required=False,
            widget=RightsSelectWidget,
            choices=RIGHTS_CHOICES,
            initial=settings.BDR_ADMIN
    )

    def build_rights(self):
        rights_builder = RightsBuilder()
        [rights_builder.addReader(identity) for identity in self.cleaned_data['discover_and_read']]
        [rights_builder.addDiscoverer(identity) for identity in self.cleaned_data['discover_and_read']]
        [rights_builder.addReader(identity) for identity in self.cleaned_data['read_only']]
        [rights_builder.addDiscoverer(identity) for identity in self.cleaned_data['discover_only']]
        [rights_builder.addEditor(identity) for identity in self.cleaned_data['edit_rights']]
        [rights_builder.addOwner(identity) for identity in self.cleaned_data['owners']]
        return rights_builder.build()


class IrMetadataEditForm(forms.Form, CommonFormHelperMixin):
    collections = forms.MultipleChoiceField(
            required=False,
            choices=[(0,"NULL_COLLECTION"),],
            widget=s2forms.Select2MultipleWidget
    )


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

    visibility = forms.ChoiceField(choices=( ('private', 'Private'), ('brown', 'Brown Only'), ('public', 'Public') ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'col-md-6 col-md-offset-3'
        self.helper.add_input(Submit('submit', 'Create Stream'))


class ReorderForm(forms.Form):
    child_pids_ordered_list = forms.CharField(required=True, widget=HiddenInput)

