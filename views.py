import json
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import (
    HttpResponseRedirect,
    Http404,
)
from django.shortcuts import render
import requests

from eulfedora.server import Repository
from rdflib import URIRef
from bdrcmodels.models import CommonMetadataDO
from bdrcommon import common as bdrcommon

from . import app_settings as settings
from .models import BDR_Collection
from .forms import (
    RightsMetadataEditForm,
    IrMetadataEditForm,
    RepoLandingForm,
    FileReplacementForm,
    EditXMLForm,
    ReorderForm,
)


repo = Repository()
bdr_server = bdrcommon.BdrServer(settings.BDR_BASE)


def landing(request):
    """Landing page for this repository interface"""
    form = RepoLandingForm(request.POST or None)
    if form.is_valid():
        pid = form.cleaned_data['pid']
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(
        request,
        template_name='repo_direct/landing.html',
        dictionary={'form': form}
    )


def display(request, pid):
    obj = repo.get_object(pid, create=False)
    if not obj.exists:
        raise Http404
    template_info = {'obj': obj}
    content_models = obj.get_models()
    if URIRef('info:fedora/bdr-cmodel:implicit-set') in content_models:
        template_info['obj_type'] = 'implicit-set'
    else:
        template_info['obj_type'] = ''
    return render(
        request,
        template_name='repo_direct/display.html',
        dictionary=template_info,
    )


@login_required
def reorder(request, pid):
    form = ReorderForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            child_pids_ordered_list = form.cleaned_data['child_pids_ordered_list'].split(u',')
            pairs_param_for_api = json.dumps([(value, str(index+1)) for index, value in enumerate(child_pids_ordered_list)])
            r = requests.post(settings.REORDER_URL, data={'pairs': pairs_param_for_api})
            if r.ok:
                messages.info(request, 'New order has been submitted (allow a bit of time for the changes to appear)')
                return HttpResponseRedirect(reverse('repo_direct:display', args=(pid,)))
            else:
                raise Exception('error submitting new order')
    bdr_item = bdrcommon.BdrItem(pid, bdr_server, identities=[settings.BDR_ADMIN])
    item_data = bdr_item.data
    children = bdr_item.data['relations']['hasPart'] #[] if item has no children
    for child in children:
        child['thumbnail_url'] = '%s/%s' % (settings.THUMBNAIL_BASE_URL, child['pid'])
    return render(
        request,
        template_name='repo_direct/reorder.html',
        dictionary={
            'pid': pid,
            'brief': item_data['brief'],
            'children': children,
            'form': form,
        }
    )


@login_required
def rights_edit(request, pid, dsid):
    form = RightsMetadataEditForm(request.POST or None)
    if form.is_valid():
        new_rights = form.build_rights()
        obj = repo.get_object(pid, type=CommonMetadataDO)
        obj.rightsMD.content = new_rights
        obj.save()
        messages.info(request, 'The sharing setting for %s have changed' % (pid,), extra_tags='text-info' )
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(
        request,
        template_name='repo_direct/rights_form.html',
        dictionary={
            'form': form,
            'rights_choices': json.dumps(settings.DEFAULT_RIGHTS_CHOICES),
            'pid': pid,
            'dsid': dsid,
        }
    )

def ir_edit(request, pid, dsid):
    library_collection = BDR_Collection( collection_id=settings.LIBRARY_PARENT_FOLDER_ID)
    form = IrMetadataEditForm(request.POST or None)
    form.fields['collections'].choices = library_collection.subfolder_choices
    if form.is_valid():
        new_collections = form.cleaned_data['collections']
        obj = repo.get_object(pid, type=CommonMetadataDO)
        obj.irMD.content.collection_list = new_collections
        obj.save()
        messages.info(request, 'The collecitons for %s have changed' % (pid,), extra_tags='text-info' )
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(
        request,
        template_name ='repo_direct/edit.html',
        dictionary={
            'form': form,
            'pid': pid,
            'dsid': "irMetadata"
        }
    )


@login_required
def file_edit(request, pid, dsid):
    form = FileReplacementForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        obj = repo.get_object(pid,create=False)
        if dsid in obj.ds_list:
            datastream_obj = obj.getDatastreamObject(dsid)
            datastream_obj.content = request.FILES['replacement_file'].read()
            # use the browser-supplied mimetype for now, even though we know this is unreliable
            datastream_obj.mimetype = request.FILES['replacement_file'].content_type
            datastream_obj.label = request.FILES['replacement_file'].name
            datastream_obj.save()
            obj.save()
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(
        request,
        template_name='repo_direct/file_edit.html',
        dictionary={
            'form': form,
            'dsid': dsid,
            'pid': pid,
        }
    )


@login_required
def xml_edit(request, pid, dsid):
    request.encoding = 'utf-8'
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
    return render(
        request,
        template_name='repo_direct/xml_edit.html',
        dictionary={
            'form': form,
            'pid': pid,
            'dsid': dsid
        }
    )
