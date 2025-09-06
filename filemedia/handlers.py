import os
import uuid
import datetime
from django.conf import settings
from .utils import import_class


class BaseUploaderFileManager(object):
    def __init__(self, upload_file, upload_to=None):
        self.upload_file = upload_file
        self.upload_to = upload_to

        file_storage_class = getattr(settings, 'FILEMANAGER_FILE_STORAGE', 'django.core.files.storage.DefaultStorage')

        # File storage can either be a Storage instance (currently deprecated),
        # or a class which we should instantiate ourselves
        file_storage = import_class(file_storage_class)
        if isinstance(file_storage, type):
            # The class case
            file_storage = file_storage()
        self.file_storage = file_storage

    def get_file(self):
        return self.upload_file

    def get_full_path(self):
        return os.path.join(self.get_upload_path(), self.get_filename())

    def save_file(self):
        if not hasattr(self, 'real_path'):
            self.real_path = self.file_storage.save(self.get_full_path(), self.get_file())
        return self.real_path

    def get_url(self):
        if not hasattr(self, 'real_path'):
            return None
        else:
            return self.file_storage.url(self.real_path)

    def get_filename(self):
        raise NotImplementedError

    def get_upload_path(self):
        raise NotImplementedError

    @staticmethod
    def get_default_upload_path():
        return getattr(settings, 'FILEMEDIA_UPLOAD', 'filemedia/')


class SimpleUploader(BaseUploaderFileManager):
    def get_filename(self):
        return self.upload_file.name

    def get_upload_path(self):
        return self.upload_to or self.get_default_upload_path()


class ImagesUuidUploader(SimpleUploader):
    def get_filename(self):
        if not hasattr(self, 'filename'):
            # save filename prevents the generation of a new
            extension = self.upload_file.name.split('.')[-1]
            self.filename = '{0}.{1}'.format(uuid.uuid4(), extension)
        return self.filename

    def get_upload_path(self):
        today = datetime.datetime.today()
        path = 'images/{0}{1}{2}'.format(today.year, today.month, today.day)
        return path


class FileUuidUploader(SimpleUploader):
    def get_filename(self):
        if not hasattr(self, 'filename'):
            extension = self.upload_file.name.split('.')[-1]
            self.filename = '{0}.{1}'.format(uuid.uuid4(), extension)
        return self.filename

    def get_upload_path(self):
        today = datetime.datetime.today()
        path = 'files/{0}{1}{2}'.format(today.year, today.month, today.day)
        return path


class DateDirectoryUploader(SimpleUploader):

    def get_upload_path(self):
        today = datetime.datetime.today()
        path = '{0}-{1}-{2}'.format(today.year, today.month, today.day)
        return path
