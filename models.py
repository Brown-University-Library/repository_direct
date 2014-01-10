from django.db import models
from . import app_settings as settings
import requests

class BDR_Collection(object):
    """docstring for BDR_Collection"""
    def __init__(self, collection_id):
        super(BDR_Collection, self).__init__()
        self.id = collection_id
        self.collection_info = {}

    @property
    def info(self):
        if not self.collection_info:
            self.collection_info = self._request_info()
        return self.collection_info

    def _request_info(self):
        info = {}
        url = '%s%s/' % (settings.FOLDER_API_PUBLIC, self.id)
        r = requests.get(url, verify=False)
        if r.status_code == requests.codes.ok:
            collection_info = r.json()
            info.update(collection_info)
        return info

    @property
    def name(self):
        return self.info.get('name','No name available')

    @property
    def parents(self):
        return self.info.get('parent_folders', [])

    @property
    def subfolders(self):
        return self.info.get('child_folders', [])

    @property
    def subfolder_choices(self):
        return [(str(subfolder['id']), subfolder['name']) for subfolder in self.subfolders]
