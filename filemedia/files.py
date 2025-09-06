from __future__ import unicode_literals
from PIL import Image as PilImage, ImageFile
from django.conf import settings
from django.utils.safestring import mark_safe
from .models import Media
import os


def get_file(name=None, size=None):
    try:
        Media.objects.get(unique_name=name, type='i')
    except Media.DoesNotExist:
        no_thumb = u'/static/filemedia/img/no-thumb/td_768x512.png'
        return no_thumb
    else:
        if size == 'no':
            no_thumb = u'/static/filemedia/img/no-thumb/td_768x512.png'
            img = Media.objects.get(unique_name=name, type='i')
            image = u'/media/images/%s/%s' % (img.path, img.unique_name)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'images' + os.sep + img.path + os.sep + img.unique_name
            if os.path.exists(file):
                return image
            else:
                return no_thumb
        else:
            no_thumb = u'/static/filemedia/img/no-thumb/td_%s.png' % size
            img = Media.objects.get(unique_name=name, type='i')
            image = u'/media/images/%s/thumbnail/%s/%s' % (img.path, size, img.unique_name)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'images' + os.sep + img.path + os.sep + 'thumbnail' + os.sep + size + os.sep + img.unique_name
            if os.path.exists(file):
                return image
            else:
                return no_thumb


class ManageFile(object):
    def create_directory(self, dir):
        if not os.path.exists(dir):
            return os.makedirs(dir)

    def delete_dir_is_empety(self, dir):
        if len(os.listdir(dir)) == 0:
            os.rmdir(dir)

    def delete_file(self, path, file):
        d = path + file
        if os.path.isfile(d):
            os.remove(d)
            self.delete_dir_is_empety(path)
