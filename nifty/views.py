import json
from django.contrib.admin.sites import AdminSite, site
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from .models import Setting


class MyAdminSite(AdminSite):

    def __init__(self, *args, **kwargs):
        super(MyAdminSite, self).__init__(*args, **kwargs)
        self._registry.update(site._registry)

    def get_urls(self):
        from django.urls import include, path, re_path
        from functools import update_wrapper
        from django.views.i18n import JavaScriptCatalog
        from django.conf.urls.i18n import i18n_patterns
        # Since this module gets imported in the application's root package,
        # it cannot import models from other applications at the module level,
        # and django.contrib.contenttypes.views imports ContentType.
        from django.contrib.contenttypes import views as contenttype_views
        # from iletter.admin import EntityAdmin
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            wrapper.admin_site = self
            return update_wrapper(wrapper, view)

        # Admin-site-wide views.
        urlpatterns = [
            path("", wrap(self.index), name="index"),
            path('login/', self.login, name='login'),
            path('logout/', wrap(self.logout), name='logout'),
            path('password-change/', wrap(self.password_change, cacheable=True), name='password_change'),
            path('password-change/done/', wrap(self.password_change_done, cacheable=True), name='password_change_done', ),
            path('jsi18n/', wrap(self.i18n_javascript, cacheable=True), name='jsi18n'),
            path('jsi18n2/', JavaScriptCatalog.as_view(), name='jsi18n2'),
            path('r/<int:content_type_id>/<path:object_id>/', wrap(contenttype_views.shortcut), name='view_on_site', ),

            # My add
            path('theme-settings/', wrap(self.get_theme_settings_view), name='theme_settings'),
            path('user-profile/', wrap(self.get_user_profile_view), name='profile'),
            path('get-ajax-settings/', wrap(self.ajax_get_theme_settings_view), name='ajax_theme_settings'),
            path('change-ajax-settings/', wrap(self.ajax_change_settings_view), name='ajax_change_settings'),
        ]

        # Add in each model's views, and create a list of valid URLS for the
        # app_index
        valid_app_labels = []
        for model, model_admin in self._registry.items():
            urlpatterns += [
                path('%s/%s/' % (model._meta.app_label, model._meta.model_name), include(model_admin.urls)),
            ]
            if model._meta.app_label not in valid_app_labels:
                valid_app_labels.append(model._meta.app_label)

        # If there were ModelAdmins registered, we should have a list of app
        # labels for which we need to allow access to the app_index view,
        if valid_app_labels:
            regex = r'^(?P<app_label>' + '|'.join(valid_app_labels) + ')/$'
            urlpatterns += [
                re_path(regex, wrap(self.app_index), name='app_list'),
            ]
        return urlpatterns

    # def get_urls(self):
    #     from django.urls import path
    #     from functools import update_wrapper
    #     def wrap(view, cacheable=False):
    #         def wrapper(*args, **kwargs):
    #             return self.admin_view(view, cacheable)(*args, **kwargs)
    #
    #         wrapper.admin_site = self
    #         return update_wrapper(wrapper, view)
    #
    #     urls = super(MyAdminSite, self).get_urls()
    #
    #     my_urls = [
    #         path('theme-settings/', wrap(self.get_theme_settings_view), name='theme_settings'),
    #         path('user-profile/', wrap(self.get_user_profile_view), name='profile'),
    #         path('load-ajax-settings/', wrap(self.ajax_get_theme_settings_view), name='ajax_theme_settings'),
    #         path('update-ajax-settings/', wrap(self.ajax_update_settings_view), name='ajax_update_settings'),
    #     ]
    #
    #     return urls + my_urls

    def construct_change_message(self, request, form, formsets, add=False):
        from .utils import change_log_message
        return change_log_message(form, formsets, add, request)

    def log_change(self, request, object, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an admin LogEntry object.
        """
        from django.contrib.admin.models import LogEntry, CHANGE
        from django.contrib.admin.options import get_content_type_for_model
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=CHANGE,
            change_message=message,
        )

    def get_user_profile_view(self, request):
        from .forms import UserProfileForm
        from django.contrib.auth.models import User
        from users.models import Profile
        from django.contrib import messages
        if not request.user.has_perm('admin.profile_change'):
            raise PermissionDenied(_("Can't change your profile. Your permission is denied, please contact the Administrator."))

        if request.method == 'POST':
            form = UserProfileForm(request.user, request.POST)
            if form.is_valid():
                user = User.objects.get(pk=request.user.pk)
                user.first_name = request.POST.get('first_name')
                user.last_name = request.POST.get('last_name')
                user.email = request.POST.get('email')
                user.save()

                profile = Profile.objects.get(user=user)
                profile.gender = request.POST.get('gender')
                profile.phone_number = request.POST.get('phone_number')
                profile.address = request.POST.get('address')
                profile.place_of_birth = request.POST.get('place_of_birth')
                profile.birth_date = request.POST.get('birth_date')
                profile.facebook = request.POST.get('facebook')
                profile.twitter = request.POST.get('twitter')
                profile.google_plus = request.POST.get('google_plus')
                profile.instagram = request.POST.get('instagram')

                fo = request.POST.get('photo')
                photo = fo.split("/")
                profile.photo = photo[(len(photo) - 1)]

                profile.save()
                # change_message = self.construct_change_message(request, form, None)
                # self.log_change(request, request.user, change_message)
                msg = _('User profile changed successfully.')
                messages.success(request, msg)
                return HttpResponseRedirect(
                    reverse(
                        'admin:profile'
                    )
                )
        else:
            form = UserProfileForm(request.user)

        app_list = self.get_app_list(request)
        context = {
            'title': _('User Profile'),
            'app_list': app_list,
            'form': form,
            # 'opts': User._meta
        }
        request.current_app = 'admin'
        return TemplateResponse(request, 'admin/auth/user/profile.html', context)

    def password_change(self, request, extra_context=None):
        """
        Handle the "change password" task -- both form display and validation.
        """
        from django.contrib.admin.forms import AdminPasswordChangeForm
        from django.contrib.auth.views import PasswordChangeView

        url = reverse("admin:password_change_done", current_app=self.name)
        defaults = {
            "form_class": AdminPasswordChangeForm,
            "success_url": url,
            "extra_context": {**self.each_context(request), **(extra_context or {})},
        }
        if self.password_change_template is not None:
            defaults["template_name"] = self.password_change_template
        request.current_app = self.name
        return PasswordChangeView.as_view(**defaults)(request)

    def password_change_done(self, request, extra_context=None):
        if not request.user.has_perm('admin.user_password_change'):
            raise PermissionDenied

        return super(MyAdminSite, self).password_change_done(request, extra_context)

    def logout(self, request, extra_context=None):
        extra_context = extra_context or {}
        if super(MyAdminSite, self).logout(request, extra_context):
            return redirect('admin:login')

    def app_index_for_menu(self, request, extra_context=None):
        return super(MyAdminSite, self).index(request, extra_context)

    def index(self, request, extra_context=None):
        if request.user.has_perm('admin.index_view'):
            extra_context = {}
            return super(MyAdminSite, self).index(request, extra_context)
        else:
            return redirect(reverse(request.user.profile.redirect_url))

    def get_theme_settings_view(self, request):
        if not request.user.has_perm('admin.theme_setting'):
            raise PermissionDenied

        app_list = self.get_app_list(request)
        context = {
            'title': _('Theme Settings'),
            'app_list': app_list,
        }
        request.current_app = self.name
        return TemplateResponse(request, 'admin/settings_theme.html', context)

    def ajax_get_theme_settings_view(self, request):
        # if not request.is_ajax():
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            raise Http404(_('Page not fount'))

        if not request.user.has_perm('admin.get_theme_ajax_setting'):
            data = {
                'status': False,
                'data': u'%s' % _("Can't get theme settings. You'r permission is denied, please contact the Administrator.")
            }
            return HttpResponse(json.dumps(data), content_type='application/json')

        context = {}
        return TemplateResponse(request, 'admin/ajax_settings_theme.html', context)

    def ajax_change_settings_view(self, request):
        from django.http import HttpResponseBadRequest
        # if not request.is_ajax():
        # ✅ hanya izinkan POST
        if request.method != "POST":
            return HttpResponseBadRequest("Method not allowed")

        # ✅ hanya izinkan request AJAX
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            return HttpResponseBadRequest("Only AJAX requests are allowed")

        if not request.user.has_perm('admin.change_theme_ajax_setting'):
            data = {
                'status': False,
                'data': u'%s' % _("Can't update theme settings. You'r permission is denied, please contact the Administrator.")
            }
            return HttpResponse(json.dumps(data), content_type='application/json')

        s = Setting.objects.filter(value=request.POST.get('val'), user=request.user).get()
        s.content = request.POST.get('content')
        s.save()
        data = {
            'status': True,
            'val': request.POST.get('val'),
            'content': request.POST.get('content'),
        }
        return HttpResponse(json.dumps(data), content_type='application/json')



nifty_site = MyAdminSite()
