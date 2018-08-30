import json
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import (
    HttpResponseRedirect,
    Http404,
    HttpResponseServerError,
)
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from redis import Redis
from rq import Queue
from lxml.etree import XMLSyntaxError
from eulfedora.server import Repository
from eulfedora.models import XmlDatastreamObject
from rdflib import URIRef
from bdrcommon.resources import BDRResources

from . import app_settings as settings
from .models import BDR_Collection
from .forms import (
    RightsMetadataEditForm,
    IrMetadataEditForm,
    RepoLandingForm,
    FileReplacementForm,
    EditXMLForm,
    ReorderForm,
    ItemCollectionsForm,
    EmbargoForm,
    CreateStreamForm,
)


repo = Repository()
bdr_server = BDRResources(settings.BDR_BASE)
create_stream_queue = Queue(settings.CREATE_STREAM_QUEUE, connection=Redis())


def landing(request):
    """Landing page for this repository interface"""
    form = RepoLandingForm(request.POST or None)
    if form.is_valid():
        pid = form.cleaned_data['pid']
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(
        request,
        template_name='repo_direct/landing.html',
        context={'form': form}
    )


def _audio_video_obj(obj):
    av_content_models = [
                'info:fedora/bdr-cmodel:audio',
                'info:fedora/bdr-cmodel:video',
                'info:fedora/bdr-cmodel:audioMaster',
                'info:fedora/bdr-cmodel:aiff',
                'info:fedora/bdr-cmodel:wav',
                'info:fedora/bdr-cmodel:mp3',
                'info:fedora/bdr-cmodel:mp4',
                'info:fedora/bdr-cmodel:m4v',
                'info:fedora/bdr-cmodel:mov',
            ]
    for cm in av_content_models:
        if obj.has_model(cm):
            return True
    return False


def display(request, pid):
    obj = repo.get_object(pid, create=False)
    if not obj.exists:
        raise Http404
    template_info = {'obj': obj}
    if _audio_video_obj(obj):
        template_info['audio_video_obj'] = True
    implicit_set_cmodel = 'info:fedora/bdr-cmodel:implicit-set'
    if obj.has_model(implicit_set_cmodel):
        template_info['obj_type'] = 'implicit-set'
    else:
        template_info['obj_type'] = ''
    datastreams = [ds for ds in obj.ds_list.keys() if obj.getDatastreamObject(ds).state == 'A']
    deleted_datastreams = [ds for ds in obj.ds_list.keys() if obj.getDatastreamObject(ds).state == 'D']
    template_info['datastreams'] = datastreams
    template_info['deleted_datastreams'] = deleted_datastreams
    return render(
        request,
        template_name='repo_direct/display.html',
        context=template_info,
    )


@login_required
def reorder(request, pid):
    form = ReorderForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            child_pids_ordered_list = form.cleaned_data['child_pids_ordered_list'].split(',')
            pairs_param_for_api = json.dumps([(value, str(index+1)) for index, value in enumerate(child_pids_ordered_list)])
            r = requests.post(settings.REORDER_URL, data={'parent_pid': pid, 'child_pairs': pairs_param_for_api})
            if r.ok:
                messages.info(request, 'New order has been submitted (allow a bit of time for the changes to appear)')
                return HttpResponseRedirect(reverse('repo_direct:display', args=(pid,)))
            else:
                raise Exception('error submitting new order')
    bdr_item = bdr_server.item.get(pid, identities=[settings.BDR_ADMIN])
    item_data = bdr_item.data
    children = bdr_item.data['relations']['hasPart'] #[] if item has no children
    for child in children:
        child['thumbnail_url'] = '%s/%s/' % (settings.THUMBNAIL_BASE_URL, child['pid'])
        child['studio_url'] = '%s/%s/' % (settings.STUDIO_ITEM_URL, child['pid'])
    return render(
        request,
        template_name='repo_direct/reorder.html',
        context={
            'pid': pid,
            'brief': item_data['brief'],
            'children': children,
            'form': form,
        }
    )


def edit_item_collection(request, pid):
    if request.method == 'POST':
        form = ItemCollectionsForm(request.POST)
        if form.is_valid():
            try:
                update_ir_data(pid, form.cleaned_data['collection_ids'].split(','))
            except Exception as e:
                return HttpResponseServerError(str(e))
            messages.info(request, f'Collection IDs for {pid} updated to "{form.cleaned_data["collection_ids"]}"')
            return HttpResponseRedirect(reverse('repo_direct:display', args=(pid,)))
    else:
        form = ItemCollectionsForm.from_storage_data(pid)
    return render(
            request,
            template_name='repo_direct/edit_item_collection.html',
            context={'pid': pid, 'form': form}
        )


def _post_embargo_year_to_api(pid, year):
    params = {'pid': pid}
    embargo_end = f'{year}-06-01T00:00:01Z'
    params['rels'] = json.dumps({'embargo_end': embargo_end})
    r = requests.put(settings.ITEM_POST_URL, data=params)
    if not r.ok:
        err_msg = 'error saving new embargo end year:\n'
        err_msg += f'{r.status_code} - {r.text}'
        raise Exception(err_msg)


def embargo(request, pid):
    if request.method == 'POST':
        form = EmbargoForm(request.POST)
        if form.is_valid():
            _post_embargo_year_to_api(pid, form.cleaned_data['new_embargo_end_year'])
            messages.info(request, f'{form.cleaned_data["new_embargo_end_year"]} added.')
            return HttpResponseRedirect(reverse('repo_direct:display', args=(pid,)))
    else:
        form = EmbargoForm()
    return render(
            request,
            template_name='repo_direct/embargo.html',
            context={'pid': pid, 'form': form}
        )


def _queue_stream_job(pid, visibility=None):
    job = create_stream_queue.enqueue_call(func='stream_objects.create',
                    args=(pid,), kwargs={'rights_setting': visibility},
                    timeout=40000)
    return job.id


def create_stream(request, pid):
    if request.method == 'POST':
        form = CreateStreamForm(request.POST)
        if form.is_valid():
            _queue_stream_job(pid, visibility=form.cleaned_data['visibility'])
            return HttpResponseRedirect(reverse('repo_direct:display', args=(pid,)))
    else:
        form = CreateStreamForm()
    return render(
            request,
            template_name='repo_direct/create_stream.html',
            context={'pid': pid, 'form': form}
        )


@login_required
def rights_edit(request, pid, dsid):
    form = RightsMetadataEditForm(request.POST or None)
    if form.is_valid():
        new_rights = form.build_rights()
        params = {'pid': pid}
        params['rights'] = json.dumps({'xml_data': new_rights.serialize().decode('utf8')})
        r = requests.put(settings.ITEM_POST_URL, data=params)
        if not r.ok:
            err_msg = f'error saving {dsid} content\n'
            err_msg += f'{r.status_code} - {r.text}'
            return HttpResponseServerError(err_msg)
        messages.info(request, 'The sharing setting for %s have changed' % (pid,), extra_tags='text-info' )
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(
        request,
        template_name='repo_direct/edit.html',
        context={
            'form': form,
            'pid': pid,
            'dsid': dsid
        }
    )


def update_ir_data(pid, collections):
    params = {'pid': pid}
    #passing collections in the form 123#123+456#456, instead of using collection name
    #   The API doesn't care about the name, but should have a better way of just passing
    #   a list of IDs.
    folders_param = '+'.join([f'{col}#{col}' for col in collections])
    params['ir'] = json.dumps({'parameters': {'folders': folders_param}})
    r = requests.put(settings.ITEM_POST_URL, data=params)
    if not r.ok:
        err_msg = 'error saving new collections information:\n'
        err_msg += f'{r.status_code} - {r.text}'
        raise Exception(err_msg)


def ir_edit(request, pid, dsid):
    library_collection = BDR_Collection( collection_id=settings.LIBRARY_PARENT_FOLDER_ID)
    form = IrMetadataEditForm(request.POST or None)
    form.fields['collections'].choices = library_collection.subfolder_choices
    if form.is_valid():
        new_collections = form.cleaned_data['collections']
        if new_collections:
            try:
                update_ir_data(pid, new_collections)
            except Exception as e:
                return HttpResponseServerError(str(e))
            messages.info(request, f'The collections for {pid} have changed', extra_tags='text-info' )
        else:
            messages.info(request, 'no collections were selected', extra_tags='text-info' )
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    messages.info(request, 'Note: this object will be removed from any current collections if you set new collections here.')
    return render(
        request,
        template_name ='repo_direct/edit.html',
        context={
            'form': form,
            'pid': pid,
            'dsid': dsid
        }
    )


@login_required
def file_edit(request, pid, dsid):
    form = FileReplacementForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        obj = repo.get_object(pid,create=False)
        if dsid in obj.ds_list:
            uploaded_file = request.FILES['replacement_file']
            file_name = uploaded_file.name
            params = {'pid': pid}
            params['content_streams'] = json.dumps(
                    [{'dsID': dsid, 'file_name': file_name}])
            params['overwrite_content'] = 'yes'
            params[file_name] = (file_name, uploaded_file)
            m = MultipartEncoder(fields=params)
            r = requests.put(settings.ITEM_POST_URL, data=m, headers={"Content-Type": m.content_type})
            if not r.ok:
                err_msg = f'error saving {dsid} content\n'
                err_msg += f'{r.status_code} - {r.text}'
                return HttpResponseServerError(err_msg)
            msg = 'Saved new %s content.' % dsid
            if dsid.lower() == 'master_tiff' or dsid.lower() == 'master':
                msg += ' Please also update any derivative files.'
            messages.info(request, msg)
        else:
            messages.error(request, 'Found no %s datastream. Please contact BDR.' % dsid)
        return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    return render(
        request,
        template_name='repo_direct/file_edit.html',
        context={
            'form': form,
            'dsid': dsid,
            'pid': pid,
        }
    )


@login_required
@require_http_methods(['GET', 'POST'])
def xml_edit(request, pid, dsid):
    request.encoding = 'utf-8'
    obj = repo.get_object(pid)
    if request.method == "POST":
        form = EditXMLForm(request.POST)
        if form.is_valid():
            xml_content = u"%s" % form.cleaned_data['xml_content']
            if dsid in ['MODS', 'rightsMetadata', 'irMetadata', 'RELS-INT', 'RELS-EXT']:
                params = {'pid': pid}
                if dsid == 'MODS':
                    params['mods'] = json.dumps({'xml_data': xml_content})
                elif dsid == 'rightsMetadata':
                    params['rights'] = json.dumps({'xml_data': xml_content})
                elif dsid == 'irMetadata':
                    params['ir'] = json.dumps({'xml_data': xml_content})
                elif dsid == 'RELS-EXT':
                    params['rels'] = json.dumps({'xml_data': xml_content})
                elif dsid == 'RELS-INT':
                    params['rels_int'] = json.dumps({'xml_data': xml_content})
                r = requests.put(settings.ITEM_POST_URL, data=params)
                if not r.ok:
                    err_msg = f'error saving {dsid} content\n'
                    err_msg += f'{r.status_code} - {r.text}'
                    return HttpResponseServerError(err_msg)
            else:
                if dsid in obj.ds_list:
                    datastream_obj = obj.getDatastreamObject(dsid)
                    datastream_obj.content = xml_content.encode('utf-8')
                    datastream_obj.save()
                else:
                    return HttpResponseServerError('%s is not a valid datastream' % dsid)
            messages.info(request, '%s datastream updated' % dsid)
            return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    elif request.method == 'GET':
        if dsid in obj.ds_list:
            datastream_obj = obj.getDatastreamObject(dsid, XmlDatastreamObject)
            try:
                xml_content = datastream_obj.content.serialize(pretty=True)
            except XMLSyntaxError as e:
                import traceback
                subject = 'error parsing XML for %s %s' % (pid, dsid)
                message = traceback.format_exc()
                mail_admins(subject, message)
                return HttpResponseServerError('couldn\'t load XML - may be invalid. BDR has been notified.')
        else:
            xml_content = 'No datastream found'
        form = EditXMLForm({'xml_content': xml_content})
    return render(
        request,
        template_name='repo_direct/edit.html',
        context={
            'form': form,
            'pid': pid,
            'dsid': dsid
        }
    )

