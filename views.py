""" Create your views here."""
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from eulfedora.server import Repository

from bdrcmodels.models import MasterImage
from bdrcmodels.models import CommonMetadataDO

from .forms import (
    UploadMasterImageForm,
    DublinCoreEditForm,
    RightsMetadataEditForm,
    RightsMetadataEditForm2,
    IrMetadataEditForm,
    get_collections_choices,
    RepoLandingForm,
    FileReplacementForm,
)
import requests
import json

def landing(request):
    """Landing page for this repository interface"""
    if request.method == "POST":
        form = RepoLandingForm(request.POST)
        if form.is_valid():
            pid = form.cleaned_data['pid']
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    elif request.method == 'GET':
        form = RepoLandingForm()
        return render_to_response('repo_direct/landing.html', {'form': form}, context_instance=RequestContext(request))


def display(request, pid):
    repo = Repository()
    obj = repo.get_object(pid, create=False)
    return render(request, 'repo_direct/display.html', {'obj': obj})

@login_required
def edit(request, pid):
    repo = Repository()
    obj = repo.get_object(pid, type=CommonMetadataDO)
    if request.method == "POST":
        form = DublinCoreEditForm(request.POST, instance=obj.dc.content)
        if form.is_valid():
            form.update_instance()
            obj.save()
    elif request.method == 'GET':
        form = DublinCoreEditForm(instance=obj.dc.content)
    return render_to_response('repo_direct/edit.html', {'form': form, 'obj': obj}, context_instance=RequestContext(request))


@login_required
def rights_edit(request, pid, dsid):
    r_choices = ['BDR_PUBLIC', 'BROWN:COMMUNITY:ALL', 'BROWN:DEPARTMENT:LIBRARY:REPOSITORY']
    form = RightsMetadataEditForm2(request.POST or None)
    if form.is_valid():
        new_rights = form.build_rights()
        repo = Repository()
        obj = repo.get_object(pid, type=CommonMetadataDO)
        obj.rightsMD.content = new_rights
        obj.save()
        messages.info(request, 'The sharing setting for %s have changed' % (pid,) )
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render( request, 'repo_direct/rights_form.html', { 
        'form': form, 
        'rights_choices': json.dumps(r_choices),
        'pid': pid,
        'dsid': dsid,
    })

def ir_edit(request, pid, dsid):
    repo = Repository()
    obj = repo.get_object(pid, type=CommonMetadataDO)
    if request.method == "POST":
        form = IrMetadataEditForm(request.POST)
        form.fields['collections'].choices = get_collections_choices()
        if form.is_valid():
            new_collections = form.cleaned_data['collections']
            obj = repo.get_object(pid, type=CommonMetadataDO)
            obj.irMD.content.collection_list = new_collections
            obj.save()
            messages.info(request,
                          'The collecitons for %s have been set to %s' % (pid, new_collections),
                          extra_tags='text-info' )
            
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    elif request.method == 'GET':
        form = IrMetadataEditForm()
        form.fields['collections'].choices = get_collections_choices()
        return render_to_response('repo_direct/edit.html',
                                  {'form': form,
                                   'obj': obj,
                                   'dsid': "irMetadata"
                                  },
                                  context_instance=RequestContext(request))

def file_edit(request, pid, dsid):
    repo = Repository()
    obj = repo.get_object(pid,create=False) 
    if request.method == 'POST':
        form = FileReplacementForm(request.POST, request.FILES)
        if form.is_valid():
            if dsid in obj.ds_list:
                datastream_obj = obj.getDatastreamObject(dsid)
                datastream_obj.content = request.FILES['replacement_file']
                # use the browser-supplied mimetype for now, even though we know this is unreliable
                datastream_obj.mimetype = request.FILES['replacement_file'].content_type
                # let's store the original file name as the datastream label
                datastream_obj.label = request.FILES['replacement_file'].name
                datastream_obj.save()
                obj.save()
            return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
        dsid="POSTED"
    elif request.method == 'GET':
        form = FileReplacementForm()
    return render_to_response('repo_direct/file_edit.html',
                              {'form': form,
                               'obj': obj,
                               'dsid': dsid
                              },
                              context_instance=RequestContext(request))


@login_required
def xml_edit(request, pid, dsid):
    from forms import EditXMLForm
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
                #datastream_obj.content = form.cleaned_data['xml_content']
                datastream_obj.save()
            obj.save()
            return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    elif request.method == 'GET':
        if dsid in obj.ds_list:
            datastream_obj = obj.getDatastreamObject(dsid)
            if dsid in ["MODS",]:
                xml_content = datastream_obj.content
            else:
                xml_content = datastream_obj.content.serialize()
        else:
            xml_content = "No datastream found"
        form = EditXMLForm({'xml_content': xml_content})
    return render(request, 'repo_direct/edit2.html', {'form': form, 'obj': obj, 'dsid': dsid}, context_instance=RequestContext(request))
