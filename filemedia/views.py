from __future__ import unicode_literals
from django.conf import settings
from django.utils.translation import ugettext as _
from django.http import JsonResponse, Http404
from django.views.generic import FormView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import force_str
from .forms import ImageForm, UploadForm
from .utils import import_class, is_module_image_installed
from .models import Media, Image
from .images import ManageImage
import os, datetime

# deal with python3 basestring
try:
    unicode = unicode
except NameError:
    basestring = (str, bytes)
else:
    basestring = basestring


class LoadImageView():
    pass


class UploadImageView(FormView):
    form_class = UploadForm
    http_method_names = ('post',)
    upload_to = getattr(settings, 'REDACTOR_UPLOAD', 'redactor/')
    upload_handler = getattr(settings, 'REDACTOR_UPLOAD_HANDLER', 'filemedia.handlers.UUIDUploader')
    auth_decorator = getattr(settings, 'REDACTOR_AUTH_DECORATOR',staff_member_required)
    tax_id = int
    file_name = None
    object_request = None
    if isinstance(auth_decorator, basestring):
        # Given decorator is string, probably because user can't import eg.
        # django.contrib.auth.decorators.login_required in settings level.
        # We are expected to import it on our own.
        auth_decorator = import_class(auth_decorator)

    @method_decorator(csrf_exempt)
    @method_decorator(auth_decorator)
    def dispatch(self, request, *args, **kwargs):
        try:
            self.tax_id = request.POST['tax']
        except:
            self.tax_id = None
        self.object_request = request
        if request.method == 'POST' and request.is_ajax():
            if not is_module_image_installed():
                data = {
                    'error': _("ImproperlyConfigured: Neither Pillow nor PIL could be imported: No module named 'Image'"),
                }
                return JsonResponse(data)

            return super(UploadImageView, self).dispatch(request, *args, **kwargs)
        else:
            raise Http404('Page not found')

    def form_invalid(self, form):
        # TODO: Needs better error messages
        try:
            error = form.errors.values()[-1][-1]
        except:
            error = _('Invalid file.')
        data = {
            'error': error,
        }
        return JsonResponse(data)

    def form_valid(self, form):
        file_ = form.cleaned_data['file']
        handler_class = import_class(self.upload_handler)
        uploader = handler_class(file_, upload_to=self.kwargs.get('upload_to', None))
        uploader.save_file()

        self.file_name = force_str(uploader.get_filename())
        return self.file_name
        # mi = ManageImage()
        #
        # today = datetime.datetime.today()
        # path_date = '{0}{1}{2}'.format(today.year, today.month, today.day)
        #
        # """
        # insert image to database
        # """
        # if self.object_request.POST.get('object_id') != 'None' and self.object_request.POST.get('object_id') != None and self.object_request.POST.get('object_id') != '':
        #     id = int(self.object_request.POST.get('object_id'))
        #     img = Media.objects.get(pk=id)
        #
        #     path = settings.MEDIA_ROOT + 'images' + os.sep + img.path + os.sep
        #     mi.delete_all_image(path, img.unique_name)
        #
        #     img.user = self.object_request.user
        #     img.file = os.sep + 'media' + os.sep + 'images' + os.sep + path_date + os.sep + file_name
        #     img.path = path_date
        #     img.unique_name = file_name
        #     img.type = 'i'
        #     img.save()
        #
        #     change_message = [{
        #         'action': 'Updated',
        #         'fields': {
        #             'name': uploader.upload_file.name,
        #             'unique_name': file_name,
        #             'path': path_date,
        #             'created_at': '%s-%s-%s' % (img.created_at.year, img.created_at.month, img.created_at.day)
        #         }
        #     }]
        #     self.log_change(self.object_request, Image.objects.get(pk=img.pk), change_message)
        # else:
        #     img = Media()
        #     img.user = self.object_request.user
        #     img.name = uploader.upload_file.name
        #     img.file = os.sep + 'media' + os.sep + 'images' + os.sep + path_date + os.sep + file_name
        #     img.path = path_date
        #     img.unique_name = file_name
        #     img.type = 'i'
        #     img.save()
        #
        #     if (self.tax_id):
        #         img.relationships.add(self.tax_id)
        #
        #     change_message = [{
        #         'action': 'Created',
        #         'fields': {
        #             'name': uploader.upload_file.name,
        #             'unique_name': file_name,
        #             'path': path_date,
        #             'created_at': '%s-%s-%s' % (img.created_at.year, img.created_at.month, img.created_at.day)
        #         }
        #     }]
        #     self.log_addition(self.object_request, Image.objects.get(pk=img.pk), change_message)
        #
        # img_dir = settings.MEDIA_ROOT + 'images' + os.sep + path_date + os.sep
        #
        # mi.comprase_image(img_dir, file_name)
        #
        # img_count = Media.objects.all().count()
        # data = {
        #     'imgcount': img_count,
        #     'imgid': img.id,
        #     'description': img.description,
        #     'filelink': img.get_image('no'),
        #     'filename': uploader.upload_file.name,
        #     'uniquename': file_name,
        #     'path_date': img.path,
        #     'image100x100': img.get_image('100x100'),
        #     'image150x150': img.get_image('150x150'),
        #     'image356x220': img.get_image('356x220'),
        #     'imagedefault': img.get_image('no'),
        #     'object_id': self.object_request.POST.get('object_id'),
        #     'current_url': self.object_request.path
        # }
        # return JsonResponse(data)

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
