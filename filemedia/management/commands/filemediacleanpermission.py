from django.core.management import BaseCommand
from django.contrib.auth.models import Permission, ContentType


class Command(BaseCommand):

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        ContentType.objects.filter(model__icontains='media').delete()

        ##################################################################################################################################

        if Permission.objects.filter(codename='change_video').count() == 1:
            admin_st = Permission.objects.get(codename='change_video')
            admin_st.content_type = ContentType.objects.get(model='video')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='change_video').delete()
            Permission(content_type=ContentType.objects.get(model='video'), codename='change_video', name='Can change video').save()

        if Permission.objects.filter(codename='delete_video').count() == 1:
            admin_st = Permission.objects.get(codename='delete_video')
            admin_st.content_type = ContentType.objects.get(model='video')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='delete_video').delete()
            Permission(content_type=ContentType.objects.get(model='video'), codename='delete_video', name='Can delete video').save()

        if Permission.objects.filter(codename='add_video').count() == 1:
            admin_st = Permission.objects.get(codename='add_video')
            admin_st.content_type = ContentType.objects.get(model='video')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='add_video').delete()
            Permission(content_type=ContentType.objects.get(model='video'), codename='add_video', name='Can add video').save()

        if Permission.objects.filter(codename='view_video').count() == 1:
            admin_st = Permission.objects.get(codename='view_video')
            admin_st.content_type = ContentType.objects.get(model='video')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='view_video').delete()
            Permission(content_type=ContentType.objects.get(model='video'), codename='view_video', name='Can view video').save()

        ##################################################################################################################################

        if Permission.objects.filter(codename='change_file').count() == 1:
            admin_st = Permission.objects.get(codename='change_file')
            admin_st.content_type = ContentType.objects.get(model='file')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='change_file').delete()
            Permission(content_type=ContentType.objects.get(model='file'), codename='change_file', name='Can change file').save()

        if Permission.objects.filter(codename='delete_file').count() == 1:
            admin_st = Permission.objects.get(codename='delete_file')
            admin_st.content_type = ContentType.objects.get(model='file')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='delete_file').delete()
            Permission(content_type=ContentType.objects.get(model='file'), codename='delete_file', name='Can delete file').save()

        if Permission.objects.filter(codename='add_file').count() == 1:
            admin_st = Permission.objects.get(codename='add_file')
            admin_st.content_type = ContentType.objects.get(model='file')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='add_file').delete()
            Permission(content_type=ContentType.objects.get(model='file'), codename='add_file', name='Can add file').save()

        if Permission.objects.filter(codename='view_file').count() == 1:
            admin_st = Permission.objects.get(codename='view_file')
            admin_st.content_type = ContentType.objects.get(model='file')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='view_file').delete()
            Permission(content_type=ContentType.objects.get(model='file'), codename='view_file', name='Can view file').save()

        if Permission.objects.filter(codename='get_file_ajax').count() == 1:
            admin_st = Permission.objects.get(codename='get_file_ajax')
            admin_st.content_type = ContentType.objects.get(model='file')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='get_file_ajax').delete()
            Permission(content_type=ContentType.objects.get(model='file'), codename='get_file_ajax', name='Can get file (ajax)').save()

        if Permission.objects.filter(codename='change_file_ajax').count() == 1:
            admin_st = Permission.objects.get(codename='change_file_ajax')
            admin_st.content_type = ContentType.objects.get(model='file')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='change_file_ajax').delete()
            Permission(content_type=ContentType.objects.get(model='file'), codename='change_file_ajax', name='Can change upload file (ajax)').save()

        if Permission.objects.filter(codename='upload_file_ajax').count() == 1:
            admin_st = Permission.objects.get(codename='upload_file_ajax')
            admin_st.content_type = ContentType.objects.get(model='file')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='upload_file_ajax').delete()
            Permission(content_type=ContentType.objects.get(model='file'), codename='upload_file_ajax', name='Can upload file (ajax)').save()

        if Permission.objects.filter(codename='download_file').count() == 1:
            admin_st = Permission.objects.get(codename='download_file')
            admin_st.content_type = ContentType.objects.get(model='file')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='download_file').delete()
            Permission(content_type=ContentType.objects.get(model='file'), codename='download_file', name='Can download file').save()

        ##################################################################################################################################

        if Permission.objects.filter(codename='change_image').count() == 1:
            admin_st = Permission.objects.get(codename='change_image')
            admin_st.content_type = ContentType.objects.get(model='image')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='change_image').delete()
            Permission(content_type=ContentType.objects.get(model='image'), codename='change_image', name='Can change image').save()

        if Permission.objects.filter(codename='delete_image').count() == 1:
            admin_st = Permission.objects.get(codename='delete_image')
            admin_st.content_type = ContentType.objects.get(model='image')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='delete_image').delete()
            Permission(content_type=ContentType.objects.get(model='image'), codename='delete_image', name='Can delete image').save()

        if Permission.objects.filter(codename='delete_image_ajax').count() == 1:
            admin_st = Permission.objects.get(codename='delete_image_ajax')
            admin_st.content_type = ContentType.objects.get(model='image')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='delete_image_ajax').delete()
            Permission(content_type=ContentType.objects.get(model='image'), codename='delete_image_ajax', name='Can delete image (ajax)').save()

        if Permission.objects.filter(codename='add_image').count() == 1:
            admin_st = Permission.objects.get(codename='add_image')
            admin_st.content_type = ContentType.objects.get(model='image')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='add_image').delete()
            Permission(content_type=ContentType.objects.get(model='image'), codename='add_image', name='Can add image').save()

        if Permission.objects.filter(codename='view_image').count() == 1:
            admin_st = Permission.objects.get(codename='add_image')
            admin_st.content_type = ContentType.objects.get(model='image')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='view_image').delete()
            Permission(content_type=ContentType.objects.get(model='image'), codename='view_image', name='Can view image').save()

        if Permission.objects.filter(codename='get_image_ajax').count() == 1:
            admin_st = Permission.objects.get(codename='get_image_ajax')
            admin_st.content_type = ContentType.objects.get(model='image')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='get_image_ajax').delete()
            Permission(content_type=ContentType.objects.get(model='image'), codename='get_image_ajax', name='Can get image (ajax)').save()

        if Permission.objects.filter(codename='change_image_ajax').count() == 1:
            admin_st = Permission.objects.get(codename='change_image_ajax')
            admin_st.content_type = ContentType.objects.get(model='image')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='change_image_ajax').delete()
            Permission(content_type=ContentType.objects.get(model='image'), codename='change_image_ajax', name='Can change upload image (ajax)').save()

        if Permission.objects.filter(codename='upload_image_ajax').count() == 1:
            admin_st = Permission.objects.get(codename='upload_image_ajax')
            admin_st.content_type = ContentType.objects.get(model='image')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='upload_image_ajax').delete()
            Permission(content_type=ContentType.objects.get(model='image'), codename='upload_image_ajax', name='Can upload image (ajax)').save()

        if Permission.objects.filter(codename='download_image').count() == 1:
            admin_st = Permission.objects.get(codename='download_image')
            admin_st.content_type = ContentType.objects.get(model='image')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='download_image').delete()
            Permission(content_type=ContentType.objects.get(model='image'), codename='download_image', name='Can download image').save()

        # Permission.objects.filter()
        print('Sukses Filemedia clean permissions.......................')
