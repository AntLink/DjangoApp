import json, os
from functools import update_wrapper
from django.http import HttpResponse, Http404
from django.utils.encoding import force_str
# from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib.admin import helpers
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.utils import flatten_fieldsets, unquote
from django.forms.formsets import all_valid
from django.utils.timezone import datetime

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.formats import date_format
from nifty.modeladmin import Admin
from nifty.views import nifty_site

from .handlers import ImagesUuidUploader, FileUuidUploader
from .models import Image, Video, File, Tags
from .forms import ImageForm, UploadForm, TagsForm, FileForm
from .images import ManageImage, thumb
from .files import ManageFile
from django.views.i18n import JavaScriptCatalog

TO_FIELD_VAR = '_to_field'
IS_POPUP_VAR = '_popup'


class TagsAdmin(Admin):
    form = TagsForm
    change_list_template = 'admin/tags/change_list.html'
    list_display = ['name', 'tags_type', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'description', 'type']
    fieldsets = [
        (None, {'fields': ('name', 'type', 'description')}),
    ]

    def get_urls(self):
        from django.urls import path
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            path('', wrap(self.changelist_view), name='%s_%s_changelist' % info),
            path('add/', wrap(self.changelist_view), name='%s_%s_add' % info),
            # path('autocomplete/', wrap(self.autocomplete_view), name='%s_%s_autocomplete' % info),
            path('<path:object_id>/history/', wrap(self.history_view), name='%s_%s_history' % info),
            path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.changelist_view), name='%s_%s_change' % info),
        ]
        return urlpatterns

    def changelist_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        is_popup = IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET

        if is_popup:
            return super(TagsAdmin, self).changeform_view(request, object_id, form_url, extra_context)

        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField("The field %s cannot be referenced." % to_field)

        model = self.model
        opts = model._meta

        if request.method == 'POST' and '_saveasnew' in request.POST:
            object_id = None

        add = object_id is None

        if add:
            # if not self.has_add_permission(request):
            #     raise PermissionDenied
            obj = None

        else:
            obj = self.get_object(request, unquote(object_id), to_field)

            # if not self.has_view_or_change_permission(request, obj):
            #     raise PermissionDenied

            if obj is None:
                return self._get_obj_does_not_exist_redirect(request, opts, object_id)

        ModelForm = self.get_form(request, obj, change=not add)
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            form_validated = form.is_valid()
            if form_validated:
                new_object = self.save_form(request, form, change=not add)
            else:
                new_object = form.instance
            formsets, inline_instances = self._create_formsets(request, new_object, change=not add)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, not add)
                self.save_related(request, form, formsets, not add)
                change_message = self.construct_change_message(request, form, formsets, add)
                if add:
                    self.log_addition(request, new_object, change_message)
                    return self.response_add(request, new_object)
                else:
                    self.log_change(request, new_object, change_message)
                    return self.response_change(request, new_object)
            else:
                form_validated = False
        else:
            if add:
                initial = self.get_changeform_initial_data(request)
                form = ModelForm(initial=initial)
                formsets, inline_instances = self._create_formsets(request, form.instance, change=False)
            else:
                form = ModelForm(instance=obj)
                formsets, inline_instances = self._create_formsets(request, obj, change=True)

        if not add and not self.has_change_permission(request, obj):
            readonly_fields = flatten_fieldsets(self.get_fieldsets(request, obj))
        else:
            readonly_fields = self.get_readonly_fields(request, obj)
        adminForm = helpers.AdminForm(
            form,
            list(self.get_fieldsets(request, obj)),
            self.get_prepopulated_fields(request, obj),
            readonly_fields,
            model_admin=self)
        media = self.media + adminForm.media
        inline_formsets = self.get_inline_formsets(request, formsets, inline_instances, obj)
        for inline_formset in inline_formsets:
            media = media + inline_formset.media

        if request.method == 'POST' and not form_validated and "_saveasnew" in request.POST:
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False
            # Use the change template instead of the add template.
            add = False
        extra_context['add'] = add
        extra_context['change'] = not add
        extra_context['save_as'] = self.save_as
        extra_context['has_editable_inline_admin_formsets'] = False,
        extra_context['has_view_permission'] = self.has_view_permission(request, obj)
        extra_context['has_add_permission'] = self.has_add_permission(request)
        extra_context['has_change_permission'] = self.has_change_permission(request, obj)
        extra_context['has_delete_permission'] = self.has_delete_permission(request, obj)

        extra_context['adminform'] = adminForm
        extra_context['is_popup'] = is_popup
        return super(TagsAdmin, self).changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        super(TagsAdmin, self).save_model(request, obj, form, change)

    def get_queryset(self, request):
        if request.user.is_superuser:
            return self.model.objects.filter().all()
        else:
            return self.model.objects.filter(user=request.user)


class ImageAdmin(Admin):
    user_req = None
    form = ImageForm
    list_display_links = None
    tax = None
    change_list_template = 'admin/image/change_list.html'
    change_form_template = 'admin/image/change_form.html'
    search_fields = ['name', 'description', 'relationships__name']
    list_display = ['images', 'name', 'user', 'created_at']
    # list_filter = ['created_at']
    filter_horizontal = ('relationships',)
    fieldsets = [
        (None, {'fields': ('name', 'image', 'relationships', 'description')}),
    ]

    def get_urls(self):
        # from .api import views
        # from rest_framework import routers
        from django.urls import path, include

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        # router = routers.DefaultRouter()
        # router.register(r'images', views.ImageViewSet, basename='%s-%s' % info)
        # router.register(r'tags', views.ImageTagsViewSet, basename='%s-%s-tags' % info)

        urlpatterns = [
            path('', wrap(self.changelist_view), name='%s_%s_changelist' % info),
            # path('api/', include(router.urls)),
            path('jsi18n/', JavaScriptCatalog.as_view(), name='%s_%s_jsi18n' % info),
            # url(r'^(?P<mode>.*)', wrap(self.changegrid_view), name='%s_%s_changegrid' % info),
            # path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            # path('test/', wrap(self.load_image), name='%s_%s_test' % info),
            path('ajax-get/', wrap(self.ajax_get_images_view), name='%s_%s_ajax_gets' % info),
            path('redactor-get/', wrap(self.ajax_get_redactor_images), name='%s_%s_ajax_redactor_gets' % info),
            path('ajax-change/', wrap(self.ajax_image_change_view), name='%s_%s_ajax_change' % info),
            path('ajax-upload/', wrap(self.ajax_image_upload_view), name='%s_%s_ajax_uploads' % info),
            path('ajax-delete/', wrap(self.ajax_image_delete_view), name='%s_%s_ajax_delete' % info),

            path('<path:tax>/tags/', wrap(self.changelist_view), name='%s_%s_tags_changelist' % info),
            path('<path:tax>/mode/<path:mode>/', wrap(self.changelist_view), name='%s_%s_tags_mode_changelist' % info),
            path('per-page-tax/<path:perpage>/<path:tax>/<path:mode>/', wrap(self.changelist_view), name='%s_%s_tags_perpage_changelist' % info),
            path('per-page-mode/<path:perpage>/<path:mode>', wrap(self.changelist_view), name='%s_%s_mode_perpage_changelist' % info),

            path(r'mode/<path:mode>/', wrap(self.changelist_view), name='%s_%s_mode_changelist' % info),
            path(r'per-page/<path:perpage>/', wrap(self.changelist_view), name='%s_%s_perpage_changelist' % info),

            # path('autocomplete/', wrap(self.autocomplete_view), name='%s_%s_autocomplete' % info),
            path('<path:object_id>/history/', wrap(self.history_view), name='%s_%s_history' % info),
            path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view), name='%s_%s_change' % info),
            path('<path:object_id>/download/', wrap(self.download_view), name='%s_%s_download' % info),
        ]
        return urlpatterns

    @csrf_exempt
    def file_preview(request, file_id):
        try:
            # Ganti dengan model file Anda
            from .models import FileMedia
            file_obj = FileMedia.objects.get(id=file_id)
            file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)

            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                # Tentukan content type berdasarkan ekstensi file
                file_name = file_obj.file.name.lower()
                if file_name.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif file_name.endswith('.doc') or file_name.endswith('.docx'):
                    content_type = 'application/msword'
                elif file_name.endswith('.xls') or file_name.endswith('.xlsx'):
                    content_type = 'application/vnd.ms-excel'
                elif file_name.endswith('.ppt') or file_name.endswith('.pptx'):
                    content_type = 'application/vnd.ms-powerpoint'
                else:
                    content_type = 'application/octet-stream'

                response = HttpResponse(file_content, content_type=content_type)
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                # Tambahkan header untuk mengizinkan akses dari domain eksternal
                response['Access-Control-Allow-Origin'] = '*'
                return response
            else:
                raise Http404("File not found")
        except Exception as e:
            print(f"Error loading file: {e}")
            raise Http404("Error loading file")
    def changelist_view(self, request, extra_context=None, tax=None, mode=None):
        self.user_req = request.user
        extra_context = extra_context or {}
        tax_name = None
        self.tax = tax
        taxint = int
        if not tax == None:
            try:
                taxint = int(self.tax)
            except ValueError:
                raise Http404

            try:
                tax_name = self.get_tax_name_by_id(self.tax)
            except ObjectDoesNotExist:
                raise Http404

        if mode == 'grid':
            self.list_display = ['thumbnail']
        else:
            self.list_display = ['images']

        selected = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)
        actions = self.get_actions(request)
        # Actions with confirmation
        if (actions and request.method == 'POST' and helpers.ACTION_CHECKBOX_NAME in request.POST and 'index' not in request.POST and '_save' not in request.POST):
            if selected and request.POST.get('action') == 'delete_selected':
                for id in selected:
                    self.model.objects.get(pk=id, type='p').delete_selected()

        if request.user.is_superuser:
            tags = Tags.objects.filter(type='p').all()
        else:
            tags = Tags.objects.filter(type='p', user=request.user).all()

        extra_context['tax_name'] = tax_name
        extra_context['type_url'] = mode
        extra_context['tax'] = taxint
        extra_context['tags'] = tags

        return super(ImageAdmin, self).changelist_view(request, extra_context=extra_context)

    def download_view(self, request, object_id):
        import mimetypes

        if not request.user.has_perm('filemedia.download_image'):
            raise PermissionDenied(_("Can't download image. Your permission is denied, please contact the Administrator."))

        try:
            file = File.objects.get(pk=object_id)
        except ObjectDoesNotExist:
            raise Http404

        today = datetime.now().date()
        filename = settings.BASE_DIR + os.path.sep + 'media' + os.path.sep + 'images' + os.path.sep + file.path + os.path.sep + file.unique_name
        download_name = u'%s-%s.%s' % (file.name, today, file.file_type)
        content_type = mimetypes.guess_type(filename)[0]

        if os.path.exists(filename):
            with open(filename, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type=content_type)
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(download_name)
                return response
        raise Http404

    # @method_decorator(csrf_exempt)
    def ajax_image_delete_view(self, request):
        from .images import ManageImage
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            raise Http404(_('Page not found'))

        if not request.user.has_perm('filemedia.delete_image_ajax'):
            data = {
                'status': False,
                'content': u'%s' % _("Can't delete image. <br>Your permission is denied, please contact the Administrator.")
            }
            return HttpResponse(json.dumps(data), content_type='application/json')
        img = Image.objects.get(pk=int(request.POST.get('id')))

        path = settings.MEDIA_ROOT + 'images' + os.sep + img.path + os.sep
        self.log_deletion(request, img, img.name)
        ManageImage().delete_all_image(path, img.unique_name)
        img.delete()
        data = {
            'status': True,
            'content': u'%s' % _("Image deleted successfully")
        }
        return HttpResponse(json.dumps(data), content_type='application/json')

    # @method_decorator(csrf_exempt)
    def ajax_image_upload_view(self, request):
        # if not request.is_ajax():
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            raise Http404(_('Page not found'))

        if not request.user.has_perm('filemedia.upload_image_ajax'):
            data = {
                'status': False,
                'content': u'%s' % _("Can't upload image. <br>Your permission is denied, please contact the Administrator.")
            }
            return HttpResponse(json.dumps(data), content_type='application/json')

        form = UploadForm(request.POST)
        if not form.is_valid():
            data = {
                'status': False,
                'error': _('Invalid file.'),
            }
            return HttpResponse(json.dumps(data), content_type='application/json')

        file = request.FILES.get('image')
        file_split = str(file.name).split('.')
        file_ext = file_split[len(file_split) - 1]
        uploader = ImagesUuidUploader(file, upload_to=None)
        uploader.save_file()
        file_name = force_str(uploader.get_filename())
        mi = ManageImage()
        today = datetime.today()
        path_date = '{0}{1}{2}'.format(today.year, today.month, today.day)
        if request.POST.get('object_id') != 'None' and request.POST.get('object_id') != None and request.POST.get('object_id') != '':
            id = int(request.POST.get('object_id'))
            img = Image.objects.get(pk=id)

            path = settings.MEDIA_ROOT + 'images' + os.sep + img.path + os.sep
            mi.delete_all_image(path, img.unique_name)

            img.user = request.user
            img.file = os.sep + 'media' + os.sep + 'images' + os.sep + path_date + os.sep + file_name
            img.path = path_date
            img.unique_name = file_name
            img.size = self.humanbytes(file.size)
            img.type = 'p'
            img.file_type = file_ext
            img.save()

            change_message = [{
                'action': 'Updated',
                'fields': {
                    'name': file.name,
                    'unique_name': file_name,
                    'path': path_date,
                    'created_at': img.created_at.strftime('%b. %d, %Y, %I:%M %p')
                }
            }]
            self.log_change(request, Image.objects.get(pk=img.pk), change_message)
        else:
            img = Image()
            img.user = request.user
            img.name = file.name
            img.file = os.sep + 'media' + os.sep + 'images' + os.sep + path_date + os.sep + file_name
            img.path = path_date
            img.size = self.humanbytes(file.size)
            img.unique_name = file_name
            img.type = 'p'
            img.file_type = file_ext
            img.save()

            if (request.POST.get('taxid')):
                img.relationships.add(int(request.POST.get('taxid')))

            change_message = [{
                'action': 'Created',
                'fields': {
                    'name': file.name,
                    'unique_name': file_name,
                    'path': path_date,
                    'created_at': img.created_at.strftime('%b. %d, %Y, %I:%M %p')
                }
            }]
            self.log_addition(request, Image.objects.get(pk=img.pk), change_message)

        img_dir = settings.MEDIA_ROOT + 'images' + os.sep + path_date + os.sep

        mi.comprase_image(img_dir, file_name)

        if request.user.is_superuser:
            img_count = Image.objects.filter(type='p').all().count()
        else:
            img_count = Image.objects.filter(type='p', user=request.user).all().count()

        info = self.model._meta.app_label, self.model._meta.model_name

        thmb = {}
        for t in thumb:
            wh = t.split("x")
            width = ('width' + wh[0])
            thmb.update({
                width: img.get_image(t)
            })

        data = {
            'status': True,
            'imgcount': img_count,
            'imgid': img.id,
            'description': img.description,
            'filelink': img.get_image('no'),
            'filename': file.name,
            'filesize': img.size,
            'uniquename': file_name,
            'path_date': img.path,
            'thmb': thmb,
            'imagedefault': img.get_image('no'),
            'imgchange_link': reverse('admin:%s_%s_change' % info, args=(img.id,)),
            'imgdelete_link': reverse('admin:%s_%s_delete' % info, args=(img.id,)),
            'imgview_link': reverse('admin:%s_%s_download' % info, args=(img.id,)),
            'name': img.name,
            'username': img.user.username,
            'created_at': date_format(img.created_at, "DATETIME_FORMAT"),
            'object_id': request.POST.get('object_id'),
        }

        return HttpResponse(json.dumps(data), content_type='application/json')

    def ajax_image_change_view(self, request):
        # if not request.is_ajax():
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            raise Http404(_('Page not found'))

        if not request.user.has_perm('filemedia.change_image_ajax'):
            data = {
                'status': False,
                'content': u'%s' % _("Can't change image. <br>Your permission is denied, please contact the Administrator.")
            }
            return HttpResponse(json.dumps(data), content_type='application/json')

        img = Image.objects.get(pk=request.POST.get('id'))
        img.name = request.POST.get('name')
        img.description = request.POST.get('description')
        img.save()
        thmb = {}
        for t in thumb:
            wh = t.split("x")
            width = ('width' + wh[0])
            thmb.update({
                width: img.get_image(t)
            })
        data = {
            'status': True,
            'id': request.POST.get('id'),
            'name': request.POST.get('name'),
            'des': request.POST.get('description'),
            'thmb': thmb,
            'image': img.get_image('no'),
        }

        return HttpResponse(json.dumps(data), content_type='application/json')

    def ajax_get_redactor_images(self, request):
        from django.conf import settings
        from django.core.paginator import Paginator, EmptyPage, InvalidPage
        import json
        if request.is_ajax():
            images = Media.objects.filter(type='i').values(
                'id',
                'name',
                'file',
                'description',
                'unique_name',
                'created_at'
            ).order_by('-created_at')
            paging = Paginator(images, 40)
            p = request.GET.get('page')
            try:
                img = paging.page(p)
            except (EmptyPage, InvalidPage):
                img = []

            data = []
            for image in img:
                data.append({
                    'imgid': image['id'],
                    "thumb": settings.MEDIA_URL + 'image/thumbnail/100x100/' + image['unique_name'],
                    "image": settings.MEDIA_URL + 'image/' + image['unique_name'],
                    "title": image['name'],
                    'description': image['description'],
                    'uniquename': image['unique_name'],
                })
            store = [{
                'store': data,
                'page': (int(p) + 1),
            }]
            return HttpResponse(json.dumps(store), content_type='application/json')
        else:
            raise Http404(_('Page not found'))

    def ajax_get_images_view(self, request):
        # if not request.is_ajax():
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            raise Http404(_('Page not found'))

        if not request.user.has_perm('filemedia.get_image_ajax'):
            data = {
                'status': False,
                'content': u'%s' % _("Can't get image. <br>Your permission is denied, please contact the Administrator.")
            }
            return HttpResponse(json.dumps(data), content_type='application/json')

        from django.core.paginator import Paginator, EmptyPage, InvalidPage
        if request.user.is_superuser:
            images = Image.objects.filter(type='p').order_by('-created_at')
        else:
            images = Image.objects.filter(type='p', user=request.user).order_by('-created_at')

        paging = Paginator(images, 18)
        p = request.GET.get('page')
        try:
            img = paging.page(p)
        except (EmptyPage, InvalidPage):
            img = []

        data = []
        for image in img:
            thmb = {}
            for t in thumb:
                wh = t.split("x")
                width = ('width' + wh[0])
                thmb.update({
                    width: image.get_image(t)
                })
            data.append({
                'imgid': image.id,
                'thmb': thmb,
                "image": image.get_image('no'),
                "title": image.name,
                'description': image.description,
                'uniquename': image.unique_name,
                'path_date': image.path,
            })
        pagenext = (int(p) + 1)
        pageprev = (pagenext - 2)
        store = {
            'status': True,
            'store': data,
            'pagenext': pagenext,
            'pageprev': pageprev,
            'leng': len(data)
        }
        return HttpResponse(json.dumps(store), content_type='application/json')

    def check_tax_id(self, id):
        if Tags.objects.filter(pk=id, type='p'):
            return True
        else:
            return False

    def get_tax_name_by_id(self, id):
        return Tags.objects.get(id=id, type='p').name

    def get_file_by_id(self, id):
        return Image.objects.get(id=id)

    def get_queryset(self, request):
        if self.tax:
            if request.user.is_superuser:
                return self.model.objects.filter(type='p', relationships=self.tax)
            else:
                return self.model.objects.filter(type='p', relationships=self.tax, user=request.user)
        else:
            if request.user.is_superuser:
                return self.model.objects.filter(type='p')
            else:
                return self.model.objects.filter(type='p', user=request.user)

    def humanbytes(self, B):
        B = float(B)
        KB = float(1024)
        MB = float(KB ** 2)  # 1,048,576
        GB = float(KB ** 3)  # 1,073,741,824
        TB = float(KB ** 4)  # 1,099,511,627,776

        if B < KB:
            return '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'Byte')
        elif KB <= B < MB:
            return '{0:.2f} KB'.format(B / KB)
        elif MB <= B < GB:
            return '{0:.2f} MB'.format(B / MB)
        elif GB <= B < TB:
            return '{0:.2f} GB'.format(B / GB)
        elif TB <= B:
            return '{0:.2f} TB'.format(B / TB)

    def log_addition(self, request, object, message):
        import json
        from django.contrib.admin.models import LogEntry, ADDITION
        from django.contrib.admin.options import get_content_type_for_model
        return LogEntry.objects.create(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=ADDITION,
            change_message=json.dumps(message),
        )

    def log_change(self, request, object, message):
        import json
        from django.contrib.admin.models import LogEntry, CHANGE
        from django.contrib.admin.options import get_content_type_for_model
        return LogEntry.objects.create(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=CHANGE,
            change_message=json.dumps(message),
        )

    def action_checkbox(self, obj):
        from django import forms
        checkbox = forms.CheckboxInput({'class': 'form-check-input magic-checkbox', 'id': 'list-%s' % obj.id}, lambda value: False)
        html = u'<div class="file-control" style="width: 30px;">%s</div>' % (checkbox.render(helpers.ACTION_CHECKBOX_NAME, force_str(obj.pk)))
        return mark_safe(html)

    def thumbnail(self, obj):
        c = ''
        d = ''
        v = ''
        if obj.unique_name:
            if self.user_req.has_perm('filemedia.change_image'):
                c = u'<a data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="%s" class="btn-link" href="%s">%s</a>' % (_('Change'), reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id]), '<i class="demo-pli-pen-5"></i>')
            if self.user_req.has_perm('filemedia.delete_image'):
                d = u'<a data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="%s"  class="btn-link" href="%s">%s</a>' % (_('Delete'), reverse('admin:%s_%s_delete' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id]), '<i class="demo-pli-trash"></i>')
            if self.user_req.has_perm('filemedia.download_image'):
                v = u'<a data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="%s"  target="_blank" class="btn-link" href="%s">%s</a>' % (_('Download'), reverse('admin:%s_%s_download' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id]), '<i class="demo-pli-download-from-cloud"></i>')
            l = u'<a data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="%s" class="btn-link preview-btn"  href="javascript:;"><i class="demo-psi-layout-grid"></i></a>' % _('View Image')
            img = u'<img class="card-img-top" data-id="%s" src="%s" alt="%s" data-image="%s" data-description="%s" />' % (obj.pk, obj.get_image('256x256'), obj.name, obj.get_image('no'), obj.description)
            html = u'%s <div class="img-actions"><span style="font-size:14px;">%s&nbsp;%s&nbsp;%s&nbsp;%s</span></div>' % (img, c, v, d, l)
            return mark_safe(html)
        # if obj.unique_name:
        #     # if self.user_req.has_perm('filemedia.change_image'):
        #     #     c = u'<a class="add-tooltip btn-link" title="%s" href="%s">%s</a>' % (_('Change'), reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id]), '<i class="demo-pli-pen-5"></i>')
        #     # if self.user_req.has_perm('filemedia.delete_image'):
        #     #     d = u'<a class="add-tooltip btn-link" title="%s" href="%s">%s</a>' % (_('Delete'), reverse('admin:%s_%s_delete' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id]), '<i class="demo-pli-trash"></i>')
        #     # if self.user_req.has_perm('filemedia.download_image'):
        #     #     v = u'<a target="_blank" class="add-tooltip btn-link" title="%s" href="%s">%s</a>' % (_('Download'), reverse('admin:%s_%s_download' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id]), '<i class="demo-pli-download-from-cloud"></i>')
        #
        #     img = u'<img class="card-img-top" data-id="%s" src="%s" alt="%s" data-image="%s" data-description="%s" />' % (obj.pk, obj.get_image('256x256'), obj.name, obj.get_image('no'), obj.description)
        #     # html = u'%s <div class="img-actions"><span style="font-size:14px;">%s&nbsp;%s&nbsp;%s</span></div>' % (img, c, v, d)
        #     return mark_safe(img)

    def images(self, obj):
        c = ''
        d = ''
        v = ''
        a = ''
        if obj.unique_name:
            if self.user_req.has_perm('filemedia.change_image'):
                c = u'<li><a class="btn-link" style="width:%s" href="%s"><i class="demo-pli-pen-5"></i> %s</a></li>' % ('100%', reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id]), _('Change'))

            if self.user_req.has_perm('filemedia.delete_image'):
                d = u'<li><a class="btn-link" style="width:%s" href="%s"><i class="demo-pli-trash"></i> %s</a></li>' % ('100%', reverse('admin:%s_%s_delete' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id]), _('Delete'))

            if self.user_req.has_perm('filemedia.download_image'):
                v = u'<li><a target="_blank" class="btn-link" style="width:%s" href="%s"><i class="demo-pli-download-from-cloud"></i> %s</a></li>' % ('100%', reverse('admin:%s_%s_download' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id]), _('Download'))

            if self.user_req.has_perm('filemedia.change_image') or self.user_req.has_perm('filemedia.delete_image') or self.user_req.has_perm('filemedia.download_image'):
                a = u'<div class="file-settings dropdown"><button class="btn btn-icon" data-bs-toggle="dropdown" type="button" aria-expanded="false"><i class="demo-psi-dot-vertical"></i></button> <ul class="dropdown-menu" >%s %s %s</ul></div>' % (c, d, v)

            html = u'%s<div class="file-details"><div class="media-block"><div class="media-left"><img class="img-responsive" style="width:40px" src="%s" alt="%s"/></div><div class="media-body"><p class="file-name">%s</p><small>%s | %s</small></small></div></div></div>' % (a, obj.get_image('100x100'), obj.name, obj.name, date_format(obj.created_at, "DATETIME_FORMAT"), obj.size)
            return mark_safe(html)

    images.short_description = _('Images')
    images.admin_order_field = '-name'


class FileAdmin(Admin):
    user_req = None
    form = FileForm
    # list_per_page = 10
    tax = None
    change_form_template = 'admin/file/change_form.html'
    change_list_template = 'admin/file/change_list.html'
    fieldsets = [
        (None, {'fields': ('name', 'files', 'relationships', 'description')}),
    ]
    # list_filter = ['created_at']
    list_display = ['get_name']
    search_fields = ['name', 'description']
    filter_horizontal = ('relationships',)

    def get_urls(self):
        from django.urls import path
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            path('', wrap(self.changelist_view), name='%s_%s_changelist' % info),
            path('jsi18n/', JavaScriptCatalog.as_view(), name='%s_%s_jsi18n' % info),
            # path(r'mode/<path:mode>/', wrap(self.changelist_view), name='%s_%s_mode_changelist' % info),
            # path(r'per-page/<path:perpage>/', wrap(self.changelist_view), name='%s_%s_perpage_changelist' % info),
            # url(r'^(?P<mode>.*)', wrap(self.changegrid_view), name='%s_%s_changegrid' % info),
            # path('add/', wrap(self.add_view), name='%s_%s_add' % info),

            # path('test/', wrap(self.load_image), name='%s_%s_test' % info),
            # path('ajax-get-images/', wrap(self.ajax_get_images_view), name='%s_%s_ajax_get_images' % info),
            # path('ajax-change/', wrap(self.ajax_image_change_view), name='%s_%s_ajax_image_change' % info),
            path('ajax-upload/', wrap(self.ajax_file_upload_view), name='%s_%s_ajax_uploads' % info),

            path('<path:tax>/tags/', wrap(self.changelist_view), name='%s_%s_tags_changelist' % info),
            # path('per-page-tax/<path:perpage>/<path:tax>/<path:mode>/', wrap(self.changelist_view), name='%s_%s_tags' % info),
            # path('per-page-mode/<path:perpage>/<path:mode>', wrap(self.changelist_view), name='%s_%s_perpage' % info),

            # path('autocomplete/', wrap(self.autocomplete_view), name='%s_%s_autocomplete' % info),
            path('<path:object_id>/history/', wrap(self.history_view), name='%s_%s_history' % info),
            path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view), name='%s_%s_change' % info),
            path('<path:object_id>/download/', wrap(self.download_view), name='%s_%s_download' % info),
        ]
        return urlpatterns

    def changelist_view(self, request, tax=None, extra_context=None):
        self.user_req = request.user
        extra_context = extra_context or {}
        tax_name = None
        self.tax = tax
        taxint = int
        if not self.tax == None:
            try:
                taxint = int(self.tax)
            except ValueError:
                raise Http404

            try:
                tax_name = self.get_tax_name_by_id(self.tax)
            except ObjectDoesNotExist:
                raise Http404

        selected = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)
        actions = self.get_actions(request)
        # Actions with confirmation
        if (actions and request.method == 'POST' and helpers.ACTION_CHECKBOX_NAME in request.POST and 'index' not in request.POST and '_save' not in request.POST):
            if selected and request.POST.get('action') == 'delete_selected':
                for id in selected:
                    self.model.objects.get(pk=id, type='f').delete_selected()

        if request.user.is_superuser:
            tags = Tags.objects.filter(type='f').all()
        else:
            tags = Tags.objects.filter(type='f', user=request.user).all()

        extra_context['tax_name'] = tax_name
        extra_context['tax'] = taxint
        extra_context['tags'] = tags

        return super(FileAdmin, self).changelist_view(request, extra_context=extra_context)

    # @method_decorator(csrf_exempt)
    def ajax_file_upload_view(self, request):
        # if not request.is_ajax():
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            raise Http404(_('Page not found'))

        if not request.user.has_perm('filemedia.upload_file_ajax'):
            data = {
                'status': False,
                'data': u'%s' % _("Can't upload file. <br>You'r permission is denied, please contact the Administrator.")
            }
            return HttpResponse(json.dumps(data), content_type='application/json')

        files = request.FILES.get('file')
        file_split = str(files.name).split('.')
        file_ext = file_split[len(file_split) - 1]
        uploader = FileUuidUploader(files, upload_to=None)
        uploader.save_file()
        unix_name = force_str(uploader.get_filename())

        today = datetime.today()
        path_date = '{0}{1}{2}'.format(today.year, today.month, today.day)
        if request.POST.get('object_id') != 'None' and request.POST.get('object_id') != None and request.POST.get('object_id') != '':
            id = int(request.POST.get('object_id'))
            file = File.objects.get(pk=id)

            path = settings.MEDIA_ROOT + 'files' + os.sep + file.path + os.sep
            ManageFile().delete_file(path, file.unique_name)

            file.user = request.user
            file.file = os.sep + 'media' + os.sep + 'files' + os.sep + path_date + os.sep + unix_name
            file.path = path_date
            file.name = files.name
            file.unique_name = unix_name
            file.size = self.humanbytes(files.size)
            file.type = 'f'
            file.file_type = file_ext
            file.save()

            change_message = [{
                'action': 'Updated',
                'fields': {
                    'name': file.name,
                    'unique_name': unix_name,
                    'path': path_date,
                    'created_at': file.created_at.strftime('%b. %d, %Y, %I:%M %p')
                }
            }]
            self.log_change(request, File.objects.get(pk=file.pk), change_message)
        else:
            file = File()
            file.user = request.user
            file.name = files.name
            file.file = os.sep + 'media' + os.sep + 'files' + os.sep + path_date + os.sep + unix_name
            file.path = path_date
            file.size = self.humanbytes(files.size)
            file.unique_name = unix_name
            file.type = 'f'
            file.file_type = file_ext
            file.save()

            if (request.POST.get('taxid')):
                file.relationships.add(int(request.POST.get('taxid')))

            change_message = [{
                'action': 'Created',
                'fields': {
                    'name': file.name,
                    'unique_name': unix_name,
                    'path': path_date,
                    'created_at': file.created_at.strftime('%b. %d, %Y, %I:%M %p')
                }
            }]
            self.log_addition(request, File.objects.get(pk=file.pk), change_message)

        if request.user.is_superuser:
            file_count = File.objects.filter(type='f').all().count()
        else:
            file_count = File.objects.filter(type='f', user=request.user).all().count()

        info = self.model._meta.app_label, self.model._meta.model_name

        data = {
            'status': True,
            'count': file_count,
            'id': file.id,
            'description': file.description,
            'filelink': '',
            'filesize': file.size,
            'data_type': file.file_type,
            'data_src': str(file.file),
            'filename': file.name,
            'uniquename': unix_name,
            'path_date': file.path,
            'change_link': reverse('admin:%s_%s_change' % info, args=(file.id,)),
            'delete_link': reverse('admin:%s_%s_delete' % info, args=(file.id,)),
            'download_link': reverse('admin:%s_%s_download' % info, args=(file.id,)),
            'name': file.name,
            'username': file.user.username,
            'created_at': date_format(file.created_at, "DATETIME_FORMAT"),
            'object_id': request.POST.get('object_id')
        }

        return HttpResponse(json.dumps(data), content_type='application/json')

    def download_view(self, request, object_id):
        import mimetypes

        if not request.user.has_perm('filemedia.download_file'):
            raise PermissionDenied(_("Can't download file. Your permission is denied, please contact the Administrator."))

        try:
            file = File.objects.get(pk=object_id)
        except ObjectDoesNotExist:
            raise Http404

        today = datetime.now().date()
        filename = settings.BASE_DIR + os.path.sep + 'media' + os.path.sep + 'files' + os.path.sep + file.path + os.path.sep + file.unique_name
        download_name = u'%s-%s.%s' % (file.name, today, file.file_type)
        content_type = mimetypes.guess_type(filename)[0]

        if os.path.exists(filename):
            with open(filename, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type=content_type)
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(download_name)
                return response
        raise Http404

    def get_tax_name_by_id(self, id):
        return Tags.objects.get(id=id, type='f').name

    def get_queryset(self, request):
        if self.tax:
            if request.user.is_superuser:
                return self.model.objects.filter(type='f', relationships=self.tax)
            else:
                return self.model.objects.filter(type='f', relationships=self.tax, user=request.user)
        else:
            if request.user.is_superuser:
                return self.model.objects.filter(type='f')
            else:
                return self.model.objects.filter(type='f', user=request.user)

    def get_name(self, obj):
        info = self.model._meta.app_label, self.model._meta.model_name
        dw = ''
        ch = ''
        dl = ''
        a = ''

        # Get file extension
        file_extension = obj.file_type.lower() if obj.file_type else ''
        file_name = obj.name.lower()

        # Determine if it's an image file
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
        is_image = file_extension in image_extensions or any(file_name.endswith(ext) for ext in image_extensions)

        # Get Font Awesome icon class based on file type
        def get_file_icon_class(ext):
            ext = ext.lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']:
                return None  # Will use actual image
            elif ext == 'pdf':
                return 'fas fa-file-pdf'
            elif ext in ['doc', 'docx']:
                return 'fas fa-file-word'
            elif ext in ['xls', 'xlsx']:
                return 'fas fa-file-excel'
            elif ext in ['ppt', 'pptx']:
                return 'fas fa-file-powerpoint'
            elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
                return 'fas fa-file-archive'
            elif ext in ['txt', 'md', 'csv']:
                return 'fas fa-file-alt'
            elif ext in ['mp3', 'wav', 'ogg', 'flac']:
                return 'fas fa-file-audio'
            elif ext in ['mp4', 'avi', 'mkv', 'mov', 'wmv']:
                return 'fas fa-file-video'
            else:
                return 'fas fa-file'

        icon_class = get_file_icon_class(file_extension)

        # Generate action links with Font Awesome icons
        if self.user_req.has_perm('filemedia.download_file'):
            dw = u'<li><a class="btn-link" target="_blank" href="%s" style="width: 100%%"><i class="fas fa-download"></i> %s</a></li>' % (
                reverse('admin:%s_%s_download' % info, args=(obj.id,)), _('Download'))

        if self.user_req.has_perm('filemedia.change_file'):
            ch = u'<li><a class="btn-link" href="%s" style="width: 100%%"><i class="fas fa-edit"></i> %s</a></li>' % (
                reverse('admin:%s_%s_change' % info, args=(obj.id,)), _('Change'))

        if self.user_req.has_perm('filemedia.delete_file'):
            dl = u'<li><a class="btn-link" href="%s" style="width: 100%%"><i class="fas fa-trash"></i> %s</a></li>' % (
                reverse('admin:%s_%s_delete' % info, args=(obj.id,)), _('Delete'))

        # Generate settings dropdown if any action is available
        if self.user_req.has_perm('filemedia.download_file') or self.user_req.has_perm('filemedia.change_file') or self.user_req.has_perm('filemedia.delete_file'):
            a = u'<div class="file-settings dropdown"><button class="btn btn-icon" data-bs-toggle="dropdown" type="button" aria-expanded="false"><i class="fas fa-ellipsis-v"></i></button><ul class="dropdown-menu" style="right:-6px">%s %s %s</ul></div>' % (ch, dl, dw)

        # Generate file preview section
        if is_image:
            # For image files, use the actual image
            b = u'<div class="file-details"><div class="media-block"><div class="media-left"><div style="position: relative; width: 50px; height: 50px;"><img data-type="%s" data-src="%s" class="img-responsive image-file" style="width: 50px; height: 50px; object-fit: cover; border-radius: 0.375rem; border: 1px solid rgb(222, 226, 230); cursor: default;" src="%s" alt="%s"><div class="upload-overlay"><div class="custom-spinner"></div></div></div></div><div class="media-body"><p class="file-name">%s</p><small>%s | %s</small></div></div></div>' % (
                obj.file_type, obj.file, obj.file, obj.name,
                obj.name, date_format(obj.created_at, "DATETIME_FORMAT"), obj.size)
        else:
            # For non-image files, use Font Awesome icon
            b = u'<div class="file-details"><div class="media-block"><div class="media-left"><div style="position: relative; width: 50px; height: 50px;"><div class="file-icon-container" style="width:50px; height:50px; display: flex; align-items: center; justify-content: center; border-radius: 0.375rem; border: 1px solid #dee2e6; background-color: #f8f9fa;"><i class="%s" style="font-size: 24px; color: #6c757d;" data-type="%s" data-src="%s"></i></div></div></div><div class="media-body"><p class="file-name">%s</p><small>%s | %s</small></div></div></div>' % (
                icon_class, obj.file_type,obj.file, obj.name,
                date_format(obj.created_at, "DATETIME_FORMAT"), obj.size)

        html = a + b
        return mark_safe(html)

    def get_action_choices(self, request, default_choices=[]):
        return super(FileAdmin, self).get_action_choices(request, default_choices)

    def action_checkbox(self, obj):
        from django import forms
        checkbox = forms.CheckboxInput({'class': 'form-check-input magic-checkbox', 'id': 'list-%s' % obj.id}, lambda value: False)
        html = u'<div class="file-control" style="width: 33px;">%s</div>' % (checkbox.render(helpers.ACTION_CHECKBOX_NAME, force_str(obj.pk)))
        return mark_safe(html)

    def humanbytes(self, B):
        'Return the given bytes as a human friendly KB, MB, GB, or TB string'
        B = float(B)
        KB = float(1024)
        MB = float(KB ** 2)  # 1,048,576
        GB = float(KB ** 3)  # 1,073,741,824
        TB = float(KB ** 4)  # 1,099,511,627,776

        if B < KB:
            return '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'Byte')
        elif KB <= B < MB:
            return '{0:.2f} KB'.format(B / KB)
        elif MB <= B < GB:
            return '{0:.2f} MB'.format(B / MB)
        elif GB <= B < TB:
            return '{0:.2f} GB'.format(B / GB)
        elif TB <= B:
            return '{0:.2f} TB'.format(B / TB)

    def log_addition(self, request, object, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an admin LogEntry object.
        """
        import json
        from django.contrib.admin.models import LogEntry, ADDITION
        from django.contrib.admin.options import get_content_type_for_model
        return LogEntry.objects.create(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=ADDITION,
            change_message=json.dumps(message),
        )

    def log_change(self, request, object, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an admin LogEntry object.
        """
        import json
        from django.contrib.admin.models import LogEntry, CHANGE
        from django.contrib.admin.options import get_content_type_for_model
        return LogEntry.objects.create(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=CHANGE,
            change_message=json.dumps(message),
        )


class VideoAdmin(Admin):
    def get_queryset(self, request):
        return self.model.objects.filter(type='v')


nifty_site.register(Tags, TagsAdmin)
nifty_site.register(Image, ImageAdmin)
# nifty_site.register(Video, VideoAdmin)
nifty_site.register(File, FileAdmin)
