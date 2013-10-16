"""Forms for repo application"""
from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from django.contrib.admin.widgets import AdminFileWidget

from eulxml.xmlmap.dc import DublinCore
from bdrxml import irMetadata
from bdrxml.rights import RightsBuilder
from eulxml.forms import XmlObjectForm
from common import utilities
import ace_editor


class DublinCoreEditForm(XmlObjectForm):
    """Edit form for DublinCore metadata"""
    class Meta:
        """Metadata declaration"""
        model = DublinCore
        fields = ['title', 'creator', 'date']

class FileReplacementForm( forms.Form ):
    replacement_file = forms.FileField(label="File", widget=AdminFileWidget)

class EditXMLForm( forms.Form ):
    xml_content = forms.CharField(widget=ace_editor.CodeEditorWidget(mode='xml'))

class UploadMasterImageForm(forms.Form):
    """Upload form for MasterImage Objects"""
    label = forms.CharField(
        max_length=255,  # fedora label maxes out at 255 characters
        help_text='Preliminary title for the new object. 255 characters max.'
    )
    modsFile = forms.FileField(label="MODS")
    masterFile = forms.FileField(label="MASTER")
    colorbarFile = forms.FileField(label="MASTER-COLORBAR")

#class EditIRMetadataForm(forms.Form):
    #pass

class RepoLandingForm(forms.Form):
    pid = forms.CharField(error_messages={'required': 'Please enter a pid'})

class RightsMetadataEditForm(forms.Form):
    rights_choices = [
        ('PUBLIC', 'Public'),
        ('BROWN', 'Brown Only'),
        ('ADMIN', 'Private')
    ]
    rights = forms.ChoiceField(choices=rights_choices, widget = forms.RadioSelect())

class RightsMetadataEditForm2(forms.Form):
    discover_and_read = forms.CharField(required=False)
    discover_only = forms.CharField(required=False)
    read_only = forms.CharField(required=False)
    edit_rights = forms.CharField(required=False)
    owners = forms.CharField(required=False, initial="BROWN:DEPARTMENT:LIBRARY:REPOSITORY")

    def __init__(self, *args, **kwargs):
        super(RightsMetadataEditForm2, self).__init__(*args, **kwargs)
        for myField in self.fields:
            self.fields[myField].widget.attrs['class'] = "select_rights"

    def build_rights(self):
        rights_builder = RightsBuilder()
        [rights_builder.addReader(identity) for identity in self.cleaned_data['discover_and_read'].split(',') if identity]
        [rights_builder.addDiscoverer(identity) for identity in self.cleaned_data['discover_and_read'].split(',') if identity]
        [rights_builder.addReader(identity) for identity in self.cleaned_data['read_only'].split(',') if identity]
        [rights_builder.addDiscoverer(identity) for identity in self.cleaned_data['discover_only'].strip().split(',') if identity]
        [rights_builder.addEditor(identity) for identity in self.cleaned_data['edit_rights'].strip().split(',') if identity]
        [rights_builder.addOwner(identity) for identity in self.cleaned_data['owners'].strip().split(',') if identity]
        return rights_builder.build()

def get_collections_choices():
    folder_info = utilities.get_folder_info()
    child_folders = folder_info.get('child_folders', [])
    return [(str(cf['id']), cf['name']) for cf in child_folders]

class IrMetadataEditForm(forms.Form):
    collections = forms.MultipleChoiceField( choices=[(0,"NULL_COLLECTION"),], 
                                            widget=CheckboxSelectMultiple)
    #def __init__(self, *args, **kwargs):
        #self.fields['collections'].choices = get_collections_choices()
