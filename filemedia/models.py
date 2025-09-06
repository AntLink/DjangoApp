import os
from django.db import models
from django.urls import reverse
# from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from django.utils.safestring import mark_safe
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from django.utils.formats import date_format


class Tags(MPTTModel):
    icon_model = 'demo-pli-tag'

    user = models.ForeignKey(User, verbose_name=_('Author'), blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(_('Name'), max_length=50, unique=False)
    parent = TreeForeignKey('self', verbose_name=_('Parent'), null=True, blank=True, on_delete=models.SET_NULL, related_name='ant_tags_children')
    slug = models.SlugField(_('Slug'), max_length=35, null=True, unique=False, help_text=_('A short label, generally used in URLs.'))
    status = models.BooleanField(_('Status'), max_length=1, default=True, help_text=_('Status is checked will be published.'))
    type = models.CharField(_('Type'), max_length=1, choices=(('p', _('Picture')), ('f', _('File')), ('v', _('Video'))))
    description = models.TextField(_('Description'), max_length=255, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class MPTTMeta:
        level_attr = 'mptt_level'
        order_insertion_by = ['name']

    class Meta:
        db_table = 'ant_media_tags'
        verbose_name = _('tags')
        verbose_name_plural = _('tags')

    def __str__(self):
        return self.name

    def uuid(self):
        return get_random_string(9)

    def tags_type(self):
        type = {
            'p': _('Pictures'),
            'f': _('File'),
            'v': _('Video'),
        }
        return mark_safe(type[self.type])

    tags_type.short_description = _('Type')
    tags_type.admin_order_field = '-type'


class Media(models.Model):
    user = models.ForeignKey(User, verbose_name=_('Author'), blank=True, null=True, on_delete=models.SET_NULL)
    relationships = models.ManyToManyField(Tags, blank=True, verbose_name=_('Tags'))
    name = models.CharField(_('Name'), max_length=255)
    unique_name = models.CharField(_('Unique Name'), max_length=255)
    size = models.CharField(_('Size'), max_length=255)
    path = models.TextField(_('Path'), blank=True)
    file = models.FileField(_('File'), max_length=255, blank=True)
    type = models.CharField(_('Type'), max_length=1, blank=True, choices=(('p', _('Pictures')), ('f', _('Files')), ('v', _('Video'))))
    file_type = models.CharField(_('File type'), max_length=50)
    favored = models.BooleanField(_('Favored'), default=False)
    description = models.CharField(_('Description'), max_length=255, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        db_table = 'ant_media'
        verbose_name = _('media')
        verbose_name_plural = _('media')

    def __str__(self):
        return self.name


class Image(Media):
    icon_model = 'demo-pli-file-pictures'
    class Meta:
        proxy = True
        verbose_name = _('picture')
        verbose_name_plural = _('pictures')
        permissions = (
            ('get_image_ajax', _('Can get image (ajax)')),
            ('change_image_ajax', _('Can change upload image (ajax)')),
            ('upload_image_ajax', _('Can upload image (ajax)')),
            ('delete_image_ajax', _('Can delete image (ajax)')),
            ('download_image', _('Can download image')),
        )

    def datetime(self):
        return self.created_at.strftime('%b. %d, %Y, %I:%M %p')

    def delete(self, *args, **kwargs):
        from .images import ManageImage
        initial = super(Image, self).delete(*args, **kwargs)
        path = settings.MEDIA_ROOT + 'images' + os.sep + self.path + os.sep
        ManageImage().delete_all_image(path, self.unique_name)
        return initial

    def delete_selected(self):
        from .images import ManageImage
        path = settings.MEDIA_ROOT + 'images' + os.sep + self.path + os.sep
        return ManageImage().delete_all_image(path, self.unique_name)

    def get_image(self, size=None):
        if size == 'no':
            no_thumb = u'/static/admin/filemedia/img/no-thumb/td_768x512.png'
            image = u'/media/images/%s/%s' % (self.path, self.unique_name)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'images' + os.sep + self.path + os.sep + self.unique_name
            if os.path.exists(file):
                return mark_safe(image)
            else:
                return mark_safe(no_thumb)
        else:
            no_thumb = u'/static/admin/filemedia/img/no-thumb/td_%s.png' % size
            image = u'/media/images/%s/thumbnail/%s/%s' % (self.path, size, self.unique_name)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'images' + os.sep + self.path + os.sep + 'thumbnail' + os.sep + size + os.sep + self.unique_name
            if os.path.exists(file):
                return mark_safe(image)
            else:
                return mark_safe(no_thumb)

    def tags(self):
        html = "&nbsp;".join([u'<a href="%s" class="btn-link"><span class="label label-info">%s</span></a>' % (reverse('admin:%s_%s_tags' % (self._meta.app_label, self._meta.model_name), args=[p.pk, 'list']), p.name) for p in self.relationships.all()])
        return mark_safe(html)

    tags.short_description = _('Tags')
    tags.admin_order_field = '-name'

    datetime.short_description = _('Uploaded')
    datetime.admin_order_field = '-created_at'


class Video(Media):
    class Meta:
        proxy = True
        verbose_name = _('video')
        verbose_name_plural = _('videos')


class File(Media):
    icon_model = 'demo-pli-file'
    class Meta:
        proxy = True
        verbose_name = _('file')
        verbose_name_plural = _('files')
        permissions = (
            ('get_file_ajax', _('Can get file (ajax)')),
            ('change_file_ajax', _('Can change upload file (ajax)')),
            ('upload_file_ajax', _('Can upload file (ajax)')),
            ('download_file', _('Can download file')),
        )

    def delete(self, *args, **kwargs):
        from .files import ManageFile
        initial = super(File, self).delete(*args, **kwargs)
        path = settings.MEDIA_ROOT + 'files' + os.sep + self.path + os.sep
        ManageFile().delete_file(path, self.unique_name)
        return initial

    def delete_selected(self):
        from .files import ManageFile
        path = settings.MEDIA_ROOT + 'files' + os.sep + self.path + os.sep
        return ManageFile().delete_file(path, self.unique_name)


class Mediahastags(models.Model):
    media = models.ForeignKey(Media, related_name='membership', on_delete=models.CASCADE)
    tags = models.ForeignKey(Tags, related_name='membership', on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s is in group %s (as %s)" % (self.tags, self.media)


