from .modeladmin import Admin
from django.contrib import messages
from django.utils.translation import gettext, gettext_lazy as _
from django.template.response import TemplateResponse
from django.urls import path, reverse

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from functools import update_wrapper
from .forms import SiteSettingForm, AdminSettingForm
from .models import Site, Admin as AdminSetting

class AdminSettingAdmin(Admin):
    change_admin_form = AdminSettingForm
    fieldsets = (
        (None, {
            'fields': ('name', 'content')
        }),
    )

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            path('', wrap(self.changelist_view), name='%s_%s_changelist' % info),
            # path('add/', wrap(self.add_view), name='%s_%s_add' % info),

        ]
        return urlpatterns

    def get_queryset(self, request):
        return self.model.objects.filter(type="admin")

    def changelist_view(self, request, extra_context=None):

        opts = self.model._meta
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        if request.method == 'POST':
            form = self.change_admin_form(request.user, AdminSetting, request.POST)
            if form.is_valid():
                form.save()
                # change_message = self.construct_change_message(request, form, None)
                # self.log_change(request, request.user, change_message)
                msg = gettext('Admin setting changed successfully.')
                messages.success(request, msg)
                return HttpResponseRedirect(
                    reverse(
                        '%s:%s_%s_changelist' % (
                            self.admin_site.name,
                            self.model._meta.app_label,
                            self.model._meta.model_name,
                        ),
                    )
                )
        else:
            form = self.change_admin_form(request.user, AdminSetting)

        request.current_app = self.admin_site.name
        context = {
            'title': _('Admin Setting'),
            'app_label': opts.app_label,
            'form': form,
            'opts': opts,
        }
        return TemplateResponse(request, 'admin_set/change_form.html', context)


class SiteSettingAdmin(Admin):
    change_general_form = SiteSettingForm
    fieldsets = (
        (None, {
            'fields': ('name', 'content')
        }),
    )

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            path('', wrap(self.changelist_view), name='%s_%s_changelist' % info),
            # path('add/', wrap(self.add_view), name='%s_%s_add' % info),

        ]
        return urlpatterns

    def get_queryset(self, request):
        return self.model.objects.filter(type="site")

    def changelist_view(self, request, extra_context=None):
        opts = self.model._meta
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        if request.method == 'POST':
            form = self.change_general_form(request.user, Site, request.POST)
            if form.is_valid():
                form.save()
                # change_message = self.construct_change_message(request, form, None)
                # self.log_change(request, request.user, change_message)
                msg = gettext('Site setting changed successfully.')
                messages.success(request, msg)
                return HttpResponseRedirect(
                    reverse(
                        '%s:%s_%s_changelist' % (
                            self.admin_site.name,
                            self.model._meta.app_label,
                            self.model._meta.model_name,
                        ),
                    )
                )
        else:
            form = self.change_general_form(request.user, Site)

        request.current_app = self.admin_site.name
        context = {
            'title': _('Site Setting'),
            'app_label': opts.app_label,
            'form': form,
            'opts': opts,
        }
        return TemplateResponse(request, 'site_set/change_form.html', context)

    # def has_add_permission(self, request):
    #     return False
    #
    # def has_delete_permission(self, request, obj=None):
    #     return False
    #
    # def has_change_permission(self, request, obj=None):
    #     return False

    # def has_view_or_change_permission(self, request, obj=None):
    #     return False
