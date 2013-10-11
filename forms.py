"""Forms for repo application"""
from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from django.contrib.admin.widgets import AdminFileWidget

from eulxml.xmlmap.dc import DublinCore
from bdrxml import irMetadata
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


def get_collections_choices():
    folder_info = utilities.get_folder_info()
    child_folders = folder_info.get('child_folders', [])
    return [(str(cf['id']), cf['name']) for cf in child_folders]

class IrMetadataEditForm(forms.Form):
    collections = forms.MultipleChoiceField( choices=[(0,"NULL_COLLECTION"),], 
                                            widget=CheckboxSelectMultiple)
    #def __init__(self, *args, **kwargs):
        #self.fields['collections'].choices = get_collections_choices()
