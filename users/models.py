import os
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
# from filemedia.models import Media
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User, Group
from django.utils.text import capfirst


class MyPermission(Permission):
    class Meta:
        proxy = True
        verbose_name = _('permission')
        verbose_name_plural = _('permission')

    def __str__(self):
        return "%s | %s | %s" % (
            capfirst(self.content_type.app_label),
            capfirst(self.content_type),
            _(self.name),
        )


class MyUser(User):
    icon_model = 'demo-pli-male'

    class Meta:
        proxy = True
        verbose_name = _('user')
        verbose_name_plural = _('users')


class MyGroup(Group):
    icon_model = 'demo-pli-male-female'

    class Meta:
        proxy = True
        verbose_name = _('group')
        verbose_name_plural = _('groups')


class Profile(models.Model):
    user = models.OneToOneField(MyUser, verbose_name=_('Author'), on_delete=models.CASCADE, primary_key=True)
    # photo = models.TextField(verbose_name=_('Photo Profile'), blank=True, null=True)
    photo = models.ImageField(upload_to='photo/', blank=True, null=True)
    gender = models.CharField(verbose_name=_('Gender'), max_length=30, blank=True, null=True)
    address = models.TextField(verbose_name=_('Address'), blank=True, null=True)
    phone_number = models.CharField(verbose_name=_('Phone Number'), blank=True, null=True, max_length=30)
    place_of_birth = models.CharField(verbose_name=_('Phone Number'), blank=True, null=True, max_length=30)
    birth_date = models.CharField(null=True, blank=True, max_length=20)

    redirect_url = models.CharField(verbose_name=_('Default redirect URL'), blank=True, null=True, max_length=255, default='admin:index')
    web_link = models.CharField(verbose_name=_('Web Site'), blank=True, null=True, max_length=50)
    facebook = models.CharField(verbose_name=_('Facebook Page'), blank=True, null=True, max_length=50)
    twitter = models.CharField(verbose_name=_('Twitter Page'), blank=True, null=True, max_length=50)
    google_plus = models.CharField(verbose_name=_('Google Plus Page'), blank=True, null=True, max_length=50)
    instagram = models.CharField(verbose_name=_('Instagram Page'), blank=True, null=True, max_length=50)

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profile')
        db_table = 'ant_profile'

    def __str__(self):  # __unicode__ for Python 2
        return self.user.username

    def delete(self, *args, **kwargs):
        # Hapus file fisik ketika objek dihapus
        if self.photo:
            if os.path.isfile(self.photo.path):
                os.remove(self.photo.path)
        super().delete(*args, **kwargs)

    def get_image(self, size=None):

        image = u'%s' % self.photo
        return mark_safe(image)
        # try:
        #     # if self.user.is_superuser:
        #     #     media = Media.objects.get(unique_name=self.photo)
        #     # else:
        #     # media = self.user.media_set.get(unique_name=self.photo)
        #     media = Media.objects.get(unique_name=self.photo)
        # except ObjectDoesNotExist:
        #     return mark_safe(u'/static/niftyv2/img/profile-photos/3.png')
        #
        # if size == 'no':
        #     no_thumb = u'/static/filemedia/img/no-thumb/td_768x512.png'
        #     image = u'/media/images/%s/%s' % (media.path, media.unique_name)
        #     file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'images' + os.sep + media.path + os.sep + media.unique_name
        #     if os.path.exists(file):
        #         return mark_safe(image)
        #     else:
        #         return mark_safe(no_thumb)
        # else:
        #     no_thumb = u'/static/admin/filemedia/img/no-thumb/td_%s.png' % size
        #     image = u'/media/images/%s/thumbnail/%s/%s' % (media.path, size, media.unique_name)
        #     file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'images' + os.sep + media.path + os.sep + 'thumbnail' + os.sep + size + os.sep + media.unique_name
        #     if os.path.exists(file):
        #         return mark_safe(image)
        #     else:
        #         return mark_safe(no_thumb)

    def get_profile_photo(self):
        return self.get_image()


@receiver(post_save, sender=MyUser)
def create_or_update_user_profile2(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


@receiver(post_save, sender=User)
def create_or_update_user_profile1(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
