"""Forms for repo application"""
from django import forms
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput
from django.contrib.admin.widgets import AdminFileWidget

from bdrxml.rights import RightsBuilder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django_ace import AceWidget
from django_select2 import forms as s2forms

from . import app_settings as settings

RIGHTS_CHOICES = zip(
        settings.DEFAULT_RIGHTS_CHOICES,
        settings.DEFAULT_RIGHTS_CHOICES
    )

BDR_ADMIN=RIGHTS_CHOICES[-1]


class FileReplacementForm( forms.Form ):
    replacement_file = forms.FileField(label="File", widget=AdminFileWidget)


class EditXMLForm( forms.Form ):
    xml_content = forms.CharField(widget=AceWidget(mode='xml', width="100%", height="500px"))


class RepoLandingForm(forms.Form):
    pid = forms.CharField(error_messages={'required': 'Please enter a pid'})


class RightsSelectWidgetMixin(object):
    def build_attrs(self, *args, **kwargs):
        self.attrs.setdefault('data-minimum-input-length', 0)
        return super(RightsSelectWidgetMixin, self).build_attrs(*args, **kwargs)


class RightsSelectWidget(RightsSelectWidgetMixin, s2forms.Select2TagWidget):
    pass


class RightsMetadataEditForm(forms.Form):
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
            choices = RIGHTS_CHOICES,
            initial= BDR_ADMIN
    )

    def __init__(self, *args, **kwargs):
        super(RightsMetadataEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'col-md-6 col-md-offset-3'
        self.helper.add_input(Submit('submit', 'Save'))

    def build_rights(self):
        rights_builder = RightsBuilder()
        [rights_builder.addReader(identity) for identity in self.cleaned_data['discover_and_read'].split(',') if identity]
        [rights_builder.addDiscoverer(identity) for identity in self.cleaned_data['discover_and_read'].split(',') if identity]
        [rights_builder.addReader(identity) for identity in self.cleaned_data['read_only'].split(',') if identity]
        [rights_builder.addDiscoverer(identity) for identity in self.cleaned_data['discover_only'].strip().split(',') if identity]
        [rights_builder.addEditor(identity) for identity in self.cleaned_data['edit_rights'].strip().split(',') if identity]
        [rights_builder.addOwner(identity) for identity in self.cleaned_data['owners'].strip().split(',') if identity]
        return rights_builder.build()


class IrMetadataEditForm(forms.Form):
    collections = forms.MultipleChoiceField(
            required=False,
            choices=[(0,"NULL_COLLECTION"),],
            widget=CheckboxSelectMultiple
    )

class ReorderForm(forms.Form):
    child_pids_ordered_list = forms.CharField(required=True, widget=HiddenInput)
