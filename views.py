import json
import logging
import os
import tempfile
from django.core.mail import mail_admins
from django.urls import reverse
from django.contrib import messages
from django.http import (
    HttpResponseRedirect,
    Http404,
    HttpResponseServerError,
)
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import requests
from lxml.etree import XMLSyntaxError
from eulfedora.server import Repository
from eulfedora.models import XmlDatastreamObject
from rdflib import URIRef
from bdrcommon.resources import BDRResources
from bdrcommon.identity import BDR_ADMIN, BDR_ACCESS

from . import app_settings as settings
from .models import BDR_Collection
from .forms import (
    RepoLandingForm,
    FileReplacementForm,
    EditXMLForm,
    ReorderForm,
    ItemCollectionsForm,
    EmbargoForm,
    CreateStreamForm,
    AddContentFileForm,
    NewObjectForm,
)


repo = Repository()
bdr_server = BDRResources(settings.BDR_BASE)
logger = logging.getLogger('ingest')


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


def _post_new_object(form_cleaned_data):
    params = {}
    params['mods'] = json.dumps({'parameters': {'title': form_cleaned_data['title']}})
    if 'collection_id' in form_cleaned_data:
        params['ir'] = json.dumps({'parameters': {'ir_collection_id': form_cleaned_data['collection_id']}})
    params['rights'] = json.dumps({'parameters': {'owner_id': BDR_ADMIN}})
    r = requests.post(settings.ITEM_POST_URL, data=params)
    if r.ok:
        return r.json()['pid']
    else:
        raise Exception(f'error posting new object: {r.status_code} - {r.content.decode("utf8")}')


def new_object(request):
    if request.method == 'POST':
        form = NewObjectForm(request.POST)
        if form.is_valid():
            pid = _post_new_object(form.cleaned_data)
            logger.info(f'{request.user.username} created new object {pid}')
            messages.info(request, f'New object {pid} created')
            return HttpResponseRedirect(reverse('repo_direct:display', args=(pid,)))
    else:
        form = NewObjectForm()
    return render(
            request,
            template_name='repo_direct/new_object.html',
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
    bdr_item = bdr_server.item.get(pid, identities=[BDR_ADMIN])
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


def _queue_stream_job(pid, visibility):
    params = {'pid': pid}
    params['generate_derivatives'] = json.dumps({'stream': {'rights': visibility}})
    r = requests.put(settings.ITEM_POST_URL, data=params)
    if not r.ok:
        err_msg = 'error requesting stream job to be queued:\n'
        err_msg += f'{r.status_code} - {r.text}'
        raise Exception(err_msg)


def create_stream(request, pid):
    if request.method == 'POST':
        form = CreateStreamForm(request.POST)
        if form.is_valid():
            _queue_stream_job(pid, visibility=form.cleaned_data['visibility'])
            messages.info(request, 'Queued streaming derivative job.')
            return HttpResponseRedirect(reverse('repo_direct:display', args=(pid,)))
    else:
        form = CreateStreamForm()
    return render(
            request,
            template_name='repo_direct/create_stream.html',
            context={'pid': pid, 'form': form}
        )


def _post_content_file(pid, dsid, content_file, overwrite=False):
    params = {'pid': pid}
    if overwrite:
        params['overwrite_content'] = 'yes'
    content_stream = {'file_name': content_file.name}
    if dsid:
        content_stream['dsID'] = dsid
    #handle larger files that get written to a tmp directory
    if hasattr(content_file, 'temporary_file_path'):
        file_path = content_file.temporary_file_path()
        os.chmod(file_path, 0o644)
        content_stream['path'] = file_path
        params['content_streams'] = json.dumps([content_stream])
        r = requests.put(settings.ITEM_POST_URL, data=params)
    else: #handle smaller in-memory files
        params['content_streams'] = json.dumps([content_stream])
        files = {content_file.name: content_file}
        r = requests.put(settings.ITEM_POST_URL, data=params, files=files)
    return r


def add_content_file(request, pid):
    if request.method == 'POST':
        form = AddContentFileForm(request.POST, request.FILES)
        if form.is_valid():
            content_file = request.FILES['content_file']
            if form.cleaned_data['is_thumbnail']:
                dsid = 'thumbnail'
                info_msg = 'Added thumbnail'
            else:
                dsid = None
                info_msg = 'Added content'
            r = _post_content_file(pid, dsid=dsid, content_file=content_file)
            if not r.ok:
                err_msg = f'error saving content\n'
                err_msg += f'{r.status_code} - {r.text}'
                return HttpResponseServerError(err_msg)
            messages.info(request, info_msg)
            return HttpResponseRedirect(reverse('repo_direct:display', args=(pid,)))
    else:
        form = AddContentFileForm()
    return render(
            request,
            template_name='repo_direct/add_content_file.html',
            context={'pid': pid, 'form': form}
        )


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


def _get_folders_param_from_collections(collections):
    return '+'.join([f'{col.strip()}#{col.strip()}' for col in collections if col])


def update_ir_data(pid, collections):
    params = {'pid': pid}
    #passing collections in the form 123#123+456#456, instead of using collection name
    #   The API doesn't care about the name, but should have a better way of just passing
    #   a list of IDs.
    folders_param = _get_folders_param_from_collections(collections)
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


def file_edit(request, pid, dsid):
    form = FileReplacementForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        obj = repo.get_object(pid,create=False)
        if dsid in obj.ds_list:
            uploaded_file = request.FILES['replacement_file']
            r = _post_content_file(pid, dsid=dsid, content_file=uploaded_file, overwrite=True)
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
                    logger.error(err_msg)
                    raise Exception(err_msg)
            else:
                if dsid in obj.ds_list:
                    with tempfile.NamedTemporaryFile(prefix=dsid, suffix='.xml', delete=True, mode='w+b') as f:
                        f.write(xml_content.encode('utf8'))
                        f.flush()
                        f.seek(0)
                        r = _post_content_file(pid, dsid=dsid, content_file=f, overwrite=True)
                    if not r.ok:
                        err_msg = f'error saving content\n'
                        err_msg += f'{r.status_code} - {r.text}'
                        logger.error(err_msg)
                        raise Exception(err_msg)
                else:
                    err_msg = f'{dsid} is not a valid datastream'
                    logger.error(err_msg)
                    raise Exception(err_msg)
            messages.info(request, f'{dsid} datastream updated')
            return HttpResponseRedirect(reverse("repo_direct:display", args=(pid,)))
    elif request.method == 'GET':
        if dsid in obj.ds_list:
            datastream_obj = obj.getDatastreamObject(dsid, XmlDatastreamObject)
            try:
                xml_content = datastream_obj.content.serialize(pretty=True).decode('utf8')
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

