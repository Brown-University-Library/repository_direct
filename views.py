""" Create your views here."""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import (
    HttpResponseRedirect,
    HttpResponse,
)
from django.shortcuts import render

from eulfedora.server import Repository
from bdrcmodels.models import CommonMetadataDO
from bdrcmodels.models import MasterImage

from .models import BDR_Collection
from .forms import (
    RightsMetadataEditForm,
    IrMetadataEditForm,
    RepoLandingForm,
    FileReplacementForm,
    EditXMLForm,
)

import requests
import json

def landing(request):
    """Landing page for this repository interface"""
    form = RepoLandingForm(request.POST or None)
    if form.is_valid():
        pid = form.cleaned_data['pid']
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(request, 'repo_direct/landing.html', {'form': form})


def display(request, pid):
    repo = Repository()
    obj = repo.get_object(pid, create=False)
    return render(request, 'repo_direct/display.html', {'obj': obj})


@login_required
def rights_edit(request, pid, dsid):
    r_choices = ['BDR_PUBLIC', 'BROWN:COMMUNITY:ALL', 'BROWN:DEPARTMENT:LIBRARY:REPOSITORY']
    form = RightsMetadataEditForm(request.POST or None)
    if form.is_valid():
        new_rights = form.build_rights()
        repo = Repository()
        obj = repo.get_object(pid, type=CommonMetadataDO)
        obj.rightsMD.content = new_rights
        obj.save()
        messages.info(request, 'The sharing setting for %s have changed' % (pid,), extra_tags='text-info' )
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render( request, 'repo_direct/rights_form.html', { 
        'form': form, 
        'rights_choices': json.dumps(r_choices),
        'pid': pid,
        'dsid': dsid,
    })

def ir_edit(request, pid, dsid):
    repo = Repository()
    library_collection = BDR_Collection( collection_id=settings.LIBRARY_PARENT_FOLDER_ID)
    form = IrMetadataEditForm(request.POST or None)
    form.fields['collections'].choices = library_collection.subfolder_choices
    obj = repo.get_object(pid, type=CommonMetadataDO)
    if form.is_valid():
        new_collections = form.cleaned_data['collections']
        obj.irMD.content.collection_list = new_collections
        obj.save()
        messages.info(request, 'The collecitons for %s have changed' % (pid,), extra_tags='text-info' )
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(request, 'repo_direct/edit.html',{
        'form': form, 
        'obj': obj, 
        'dsid': "irMetadata" 
    })


@login_required
def file_edit(request, pid, dsid):
    repo = Repository()
    obj = repo.get_object(pid,create=False) 
    form = FileReplacementForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        if dsid in obj.ds_list:
            datastream_obj = obj.getDatastreamObject(dsid)
            datastream_obj.content = request.FILES['replacement_file'].read()
            # use the browser-supplied mimetype for now, even though we know this is unreliable
            datastream_obj.mimetype = request.FILES['replacement_file'].content_type
            datastream_obj.label = request.FILES['replacement_file'].name
            datastream_obj.save()
            obj.save()
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(request, 'repo_direct/file_edit.html',
                              {'form': form,
                               'obj': obj,
                               'dsid': dsid
                              })


@login_required
def xml_edit(request, pid, dsid):
    request.encoding = 'utf-8'
    repo = Repository()
    obj = repo.get_object(pid)
    if request.method == "POST":
        form = EditXMLForm(request.POST)
        if form.is_valid():
            if dsid in obj.ds_list:
                datastream_obj = obj.getDatastreamObject(dsid)
                xml_content = u"%s" % form.cleaned_data['xml_content']
                datastream_obj.content = xml_content.encode('utf-8')
                datastream_obj.save()
            obj.save()
            return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    elif request.method == 'GET':
        if dsid in obj.ds_list:
            datastream_obj = obj.getDatastreamObject(dsid)
            xml_content = datastream_obj.content.serialize(pretty=True)
        else:
            xml_content = "No datastream found"
        form = EditXMLForm({'xml_content': xml_content})
    return render(request, 'repo_direct/edit2.html', {
        'form': form, 
        'obj': obj, 
        'dsid': dsid
    })
