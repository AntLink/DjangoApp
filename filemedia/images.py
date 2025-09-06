from __future__ import unicode_literals
from PIL import Image as PilImage, ImageFile
from django.conf import settings
from django.utils.safestring import mark_safe
from .models import Media
import os

# ImageFile.LOAD_TRUNCATED_IMAGES = True
user_agent = [
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; 2345Explorer 5.0.0.14136)',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.108 Safari/537.36 2345Explorer/7.1.0.12633',
    'Mozilla/5.0 (Nintendo 3DS; U; ; en) Version/1.7552.EU',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1 QIHU 360SE',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.57 Safari/537.17 QIHU 360EE',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36 QIHU 360SE',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; 360SE)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Linux; U; Android-4.0.3; en-us; Galaxy Nexus Build/IML74K) AppleWebKit/535.7 (KHTML, like Gecko) CrMo/16.0.912.75 Mobile Safari/535.7',
    'Mozilla/5.0 (Linux; U; Android-4.0.3; en-us; Xoom Build/IML77) AppleWebKit/535.7 (KHTML, like Gecko) CrMo/16.0.912.75 Safari/535.7',
    'Mozilla/5.0 (Linux; Android 4.0.4; SGH-I777 Build/Task650 & Ktoonsez AOKP) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19',
    'Mozilla/5.0 (Linux; Android 4.1; Galaxy Nexus Build/JRN84D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19',
    'Mozilla/5.0 (iPhone; U; CPU iPhone OS 5_1_1 like Mac OS X; en) AppleWebKit/534.46.0 (KHTML, like Gecko) CriOS/19.0.1084.60 Mobile/9B206 Safari/7534.48.3',
    'Mozilla/5.0 (iPad; U; CPU OS 5_1_1 like Mac OS X; en-us) AppleWebKit/534.46.0 (KHTML, like Gecko) CriOS/19.0.1084.60 Mobile/9B206 Safari/7534.48.3',
    'Mozilla/5.0 (iPad; CPU OS 10_2 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/55.0.2883.79 Mobile/14C92 Safari/602.1',
    'BlackBerry8100/4.5.0.124 Profile/MIDP-2.0 Configuration/CLDC-1.1 VendorID/100',
    'BlackBerry8820/4.5.0.110 Profile/MIDP-2.0 Configuration/CLDC-1.1 VendorID/102',
    'BlackBerry9000/4.6.0.126 Profile/MIDP-2.0 Configuration/CLDC-1.1 VendorID/120',
    'BlackBerry9530/4.7.0.76 Profile/MIDP-2.0 Configuration/CLDC-1.1 VendorID/126',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) BlackBerry8703e/4.1.0 Profile/MIDP-2.0 Configuration/CLDC-1.1 VendorID/104',
    'Mozilla/5.0 (PlayBook; U; RIM Tablet OS 1.0.0; en-US) AppleWebKit/534.11 (KHTML, like Gecko) Version/7.1.0.7 Safari/534.11',
    'Mozilla/5.0 (BB10; Touch) AppleWebKit/537.10+ (KHTML, like Gecko) Version/10.1.0.4633 Mobile Safari/537.10+',
    'Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; nl) AppleWebKit/534.8+ (KHTML, like Gecko) Version/6.0.0.668 Mobile Safari/534.8+',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.0.3 Safari/602.4.8',
]


def get_image(name=None, size=None):
    try:
        Media.objects.get(unique_name=name, type='p')
    except Media.DoesNotExist:
        no_thumb = u'/static/admin/filemedia/img/no-thumb/td_768x512.png'
        return no_thumb
    else:
        if size == 'no':
            no_thumb = u'/static/admin/filemedia/img/no-thumb/td_768x512.png'
            img = Media.objects.get(unique_name=name, type='p')
            image = u'/media/images/%s/%s' % (img.path, img.unique_name)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'images' + os.sep + img.path + os.sep + img.unique_name
            if os.path.exists(file):
                return image
            else:
                return no_thumb
        else:
            no_thumb = u'/static/admin/filemedia/img/no-thumb/td_%s.png' % size
            img = Media.objects.get(unique_name=name, type='p')
            image = u'/media/images/%s/thumbnail/%s/%s' % (img.path, size, img.unique_name)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'images' + os.sep + img.path + os.sep + 'thumbnail' + os.sep + size + os.sep + img.unique_name
            if os.path.exists(file):
                return image
            else:
                return no_thumb


def get_profile_image(user=None, size=None):
    from account.models import Profile
    try:
        Profile.objects.get(id=user.profile.id)
    except Profile.DoesNotExist:
        no_thumb = u'/static/img/man.png'
        return no_thumb
    else:
        if size == 'no':
            no_thumb = u'/static/img/man.png'
            img = Profile.objects.get(id=user.profile.id)
            image = u'/media/users/%s/%s' % (user.username, img.photo)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'users' + os.sep + user.username + os.sep + img.photo
            if os.path.exists(file):
                return image
            else:
                return no_thumb

        else:
            no_thumb = u'/static/img/man.png'
            img = Profile.objects.get(id=user.profile.id)
            image = u'/media/users/%s/thumbnail/%s/%s' % (user.username, size, img.photo)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'users' + os.sep + user.username + os.sep + 'thumbnail' + os.sep + size + os.sep + img.photo
            if os.path.exists(file):
                return image
            else:
                return no_thumb


def get_employe_image(user=None, size=None, key=None):
    from employe.models import EmployeMeta, Employe

    try:
        EmployeMeta.objects.get(employe=Employe.objects.get(pk=user.employe.id), value=key)
    except EmployeMeta.DoesNotExist:
        no_thumb = u'/static/img/atc.png'
        return no_thumb
    else:
        if size == 'no':
            no_thumb = u'/static/img/atc.png'
            img = EmployeMeta.objects.get(employe=Employe.objects.get(pk=user.employe.id), value=key)
            image = u'/media/users/%s/%s' % (user.username, img.content)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'users' + os.sep + user.username + os.sep + img.content
            if os.path.exists(file):
                return image
            else:
                return no_thumb

        else:
            no_thumb = u'/static/img/atc.png'
            img = EmployeMeta.objects.get(employe=Employe.objects.get(pk=user.employe.id), value=key)
            image = u'/media/users/%s/thumbnail/%s/%s' % (user.username, size, img.content)
            file = settings.BASE_DIR + os.sep + 'media' + os.sep + 'users' + os.sep + user.username + os.sep + 'thumbnail' + os.sep + size + os.sep + img.content
            if os.path.exists(file):
                return image
            else:
                return no_thumb


thumb = [
    # '768x512',
    # '741x486',
    # '696x464',
    # '696x385',
    # '630x420',
    # '534x462',
    # '533x261',
    # '356x364',
    '356x220',
    # '324x400',
    # '324x235',
    # '324x160',
    # '300x200',
    # '265x198',
    # '218x150',
    '150x150',
    '255x150',
    '256x256',
    # '100x70',
    '100x100',
    # '80x60',
]


class ManageImage(object):

    def crop_image(self, src, dst, width, hight):
        try:
            PilImage.open(src)
        except IOError:
            return False
        else:
            img = PilImage.open(src)
            w = width / 2
            h = hight / 2
            half_the_width = img.size[0] / 2
            half_the_height = img.size[1] / 2
            newimg = img.crop(
                (
                    half_the_width - w,
                    half_the_height - h,
                    half_the_width + w,
                    half_the_height + h
                )
            )
            return newimg.save(dst, quality=120)

    def resize_image_thumb(self, src, dst, width):
        size = (width, width)
        try:
            # PilImage.open(src)
            with PilImage.open(src) as img:
                img.thumbnail(size, PilImage.LANCZOS)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

                # Simpan gambar ke tujuan
                img.save(dst, quality=120)
        except IOError or OSError:
            return False
        # else:
        #     img = PilImage.open(src)
        #     img.thumbnail(size, PilImage.LANCZOS)
        #     return img.save(dst)

    def resize_image(self, src, dst, width):
        try:
            PilImage.open(src)
        except IOError or OSError:
            return False
        else:
            img = PilImage.open(src)
            wepercent = (width / float(img.size[0]))
            hsize = int((float(img.size[0]) * float(wepercent)))
            img.fit((width, hsize), PilImage.ANTIALIAS)
            return img.save(dst)

    def create_directory(self, dir):
        if not os.path.exists(dir):
            return os.makedirs(dir)

    def delete_dir_is_empety(self, dir):
        if os.path.exists(dir):
            if len(os.listdir(dir)) == 0:
                os.rmdir(dir)

    def delete_img(self, file):
        if os.path.isfile(file):
            return os.remove(file)

    def delete_all_image(self, path, name):
        self.delete_img(path + name)
        for d in thumb:
            self.delete_img(path + 'thumbnail' + os.sep + d + os.sep + name)
            self.delete_dir_is_empety(path + 'thumbnail' + os.sep + d + os.sep)
            self.delete_dir_is_empety(path + 'thumbnail' + os.sep)
        self.delete_dir_is_empety(path)

    def comprase_image(self, img_dir, file_name):
        thumb_dir = img_dir + 'thumbnail' + os.sep
        self.create_directory(thumb_dir)
        src = img_dir + file_name
        # self.resize_image_thumb(src, src, 1024)
        for dir in thumb:
            dirn = thumb_dir + dir + os.sep
            wh = dir.split("x")
            w = int(wh[0])
            h = int(wh[1])
            self.create_directory(dirn)
            self.resize_image_thumb(src, dirn + file_name, (w * 2))
            if (w == 100 and h == 100) or (w == 150 and h == 150) or (w == 255 and h == 150) or (w == 256 and h == 256):
                self.crop_image(dirn + file_name, dirn + file_name, w, h)
