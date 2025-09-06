from django.contrib import admin

from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.utils.safestring import mark_safe
from django.contrib.admin import helpers
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User, Group
from django.contrib.auth.apps import AuthConfig
from django.utils.text import capfirst

from django.views.i18n import JavaScriptCatalog

from copy import deepcopy
from nifty.forms import ActionForm
from nifty.views import nifty_site

from .models import MyGroup, MyUser, Profile

from .forms import MyUserChangeForm, MyUserAddForm, MyGroupForm


class MyUserAdmin(UserAdmin):
    add_form_template = 'admin/users/user/add_form.html'
    change_form_template = 'admin/users/user/change_form.html'
    change_user_password_template = 'admin/users/user/change_password.html'
    action_form = ActionForm
    form = MyUserChangeForm
    add_form = MyUserAddForm
    filter_horizontal = ('groups', 'user_permissions',)
    search_fields = [
        'username', 'email'
    ]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active')
    list_filter = ('is_active', 'groups',)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    fieldsets = (
        (None, {
            'classes': ('tab-general',),
            'fields': (
                'username',
                'password',
                'photo',
                'first_name',
                'last_name',
                'gender',
                'email',
                'phone_number',
                'address',
                'place_of_birth',
                'birth_date',
                'facebook',
                'twitter',
                'google_plus',
                'instagram',
            )
        }),

        (None, {
            'classes': ('tab-permissions',),
            'fields': ('redirect_url', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),

    )
    suit_form_tabs = (('general', _('Personal info')), ('permissions', _('Permissions')))

    def get_urls(self):
        from django.urls import path, include
        # from rest_framework import routers
        # from .api import views

        info = self.model._meta.app_label, self.model._meta.model_name

        # router = routers.DefaultRouter()
        # router.register(r'users', views.UserViewSet, basename='%s-%s' % info)
        # router.register(r'groups', views.GroupViewSet, base_name='groups')

        return [
            # path('api/', include(router.urls)),
            path('jsi18n/', JavaScriptCatalog.as_view(), name='%s_%s_jsi18n' % info),
            # path('api/', views.UserViewSet.as_view({'get': 'list'}), name='%s-%s' % info),
        ] + super().get_urls()

    @property
    def media(self):
        from django import forms
        from django.conf import settings
        extra = '' if settings.DEBUG else '.min'
        js = [
            # 'vendor/jquery/jquery%s.js' % extra,
            # 'jquery.init.js',
            # 'core.js',
            # 'admin/RelatedObjectLookups.js',
            # 'actions%s.js' % extra,
            # 'urlify.js',
            # 'prepopulate%s.js' % extra,
            # 'vendor/xregexp/xregexp%s.js' % extra,
        ]
        return forms.Media(js=['admin/js/%s' % url for url in js])

    def changelist_view(self, request, extra_context=None):
        if request.user.is_superuser:
            self.list_display = ['username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active']
        else:
            self.list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']

        return super(MyUserAdmin, self).changelist_view(request, extra_context)

    def construct_change_message(self, request, form, formsets, add=False):
        from nifty.utils import change_log_message
        return change_log_message(form, formsets, add, request)

    def log_deletion(self, request, object, object_repr):
        import json
        from nifty.modeladmin import date_default
        from django.contrib.admin.models import LogEntry, DELETION
        from django.contrib.admin.options import get_content_type_for_model
        change_message = []
        data = self.model.objects.filter(pk=object.pk).values()[0]

        change_message.append({
            'action': 'Deleted',
            'fields': data
        })
        return LogEntry.objects.create(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=object_repr,
            action_flag=DELETION,
            change_message=json.dumps(change_message, default=date_default),
        )

    def get_username_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:%s_%s_change' % (self.opts.app_label, self.opts.model_name), args=(obj.pk,))
        html = '<a href="%s" class="text-semibold btn-link add-tooltip" data-toggle="tooltip" data-original-title="%s %s %s">%s</a>' % (url, _('Change'), self.opts.verbose_name, obj.username, obj.username)
        return mark_safe(html)

    get_username_link.short_description = _('Username')
    get_username_link.admin_order_field = '-username'

    def get_queryset(self, request):
        qs = super(MyUserAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_superuser=0)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(MyUserAdmin, self).get_fieldsets(request, obj)
        if not obj:
            return fieldsets

        if not request.user.is_superuser:
            fieldsets = deepcopy(fieldsets)
            for fieldset in fieldsets:
                if 'is_superuser' in fieldset[1]['fields']:
                    if type(fieldset[1]['fields']) == tuple:
                        fieldset[1]['fields'] = list(fieldset[1]['fields'])
                    fieldset[1]['fields'].remove('is_superuser')
                    fieldset[1]['fields'].remove('user_permissions')
                    # fieldset[1]['fields'].remove('photo')
                    break

        return fieldsets

    def get_action_choices(self, request, default_choices=[]):
        return super(MyUserAdmin, self).get_action_choices(request, default_choices)

    def action_checkbox(self, obj):
        from django import forms
        checkbox = forms.CheckboxInput({'class': 'magic-checkbox', 'id': 'list-%s' % obj.id}, lambda value: False)
        html = u'%s<label for="list-%s" style="margin-left:7px"></label>' % (checkbox.render(helpers.ACTION_CHECKBOX_NAME, force_str(obj.pk)), obj.pk)
        return mark_safe(html)

    action_checkbox.short_description = mark_safe('<label style="margin-left:11px">#</label>')

    # def save_model(self, request, obj, form, change):
    #     super(MyUserAdmin, self).save_model(request, obj, form, change)
    #
    #     if not obj.id:
    #         from .data import load_admin_theme_setting_stores
    #         from nifty.models import Setting
    #         load_admin_theme_setting_stores(Setting, obj.id)
    #     else:
    #
    #         p = Profile.objects.get(user=obj)
    #         p.gender = request.POST.get('gender')
    #         p.address = request.POST.get('address')
    #         p.phone_number = request.POST.get('phone_number')
    #         p.place_of_birth = request.POST.get('place_of_birth')
    #         p.birthdate = request.POST.get('birthdate')
    #         p.redirect_url = request.POST.get('redirect_url')
    #         p.save()

    # def get_list_display(self, request):
    #     super(MyUserAdmin, self).get_list_display(request)
    #     if not request.user.is_superuser:
    #         self.list_display = ('get_username_link', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    #     return self.list_display


class MyGroupAdmin(GroupAdmin):
    form = MyGroupForm

    # change_form_template = 'admin/users/user/change_form.html'
    action_form = ActionForm
    list_display = ['name', 'get_permissions']
    filter_horizontal = ('permissions',)

    def get_urls(self):
        from django.urls import path, include
        # from rest_framework import routers
        # from .api import views

        info = self.model._meta.app_label, self.model._meta.model_name

        # router = routers.DefaultRouter()
        # router.register(r'users', views.UserViewSet, base_name='%s-%s' % info)
        # router.register(r'groups', views.GroupViewSet, basename='%s-%s' % info)

        return [
            # path('api/', include(router.urls)),
            path('jsi18n/', JavaScriptCatalog.as_view(), name='%s_%s_jsi18n' % info),
            # path('api/', views.UserViewSet.as_view({'get': 'list'}), name='%s-%s' % info),
        ] + super().get_urls()

    @property
    def media(self):
        from django import forms
        from django.conf import settings
        extra = '' if settings.DEBUG else '.min'
        js = [
            # 'vendor/jquery/jquery%s.js' % extra,
            # 'jquery.init.js',
            # 'core.js',
            # 'admin/RelatedObjectLookups.js',
            # 'actions%s.js' % extra,
            # 'urlify.js',
            # 'prepopulate%s.js' % extra,
            # 'vendor/xregexp/xregexp%s.js' % extra,
            # '../../nifty/js/suit.init.js',
            # '../../nifty/js/suit.js',
        ]
        return forms.Media(js=['admin/js/%s' % url for url in js])

    def construct_change_message(self, request, form, formsets, add=False):
        from nifty.utils import change_log_message
        return change_log_message(form, formsets, add, request)

    def log_deletion(self, request, object, object_repr):
        import json
        from nifty.modeladmin import date_default
        from django.contrib.admin.models import LogEntry, DELETION
        from django.contrib.admin.options import get_content_type_for_model
        change_message = []
        data = self.model.objects.filter(pk=object.pk).values()[0]

        change_message.append({
            'action': 'Deleted',
            'fields': data
        })
        return LogEntry.objects.create(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=object_repr,
            action_flag=DELETION,
            change_message=json.dumps(change_message, default=date_default),
        )

    def get_action_choices(self, request, default_choices=[]):
        return super(MyGroupAdmin, self).get_action_choices(request, default_choices)

    def action_checkbox(self, obj):
        from django import forms
        checkbox = forms.CheckboxInput({'class': 'magic-checkbox', 'id': 'list-%s' % obj.id}, lambda value: False)
        html = u'%s<label for="list-%s" style="margin-left:7px"></label>' % (checkbox.render(helpers.ACTION_CHECKBOX_NAME, force_str(obj.pk)), obj.pk)
        return mark_safe(html)

    action_checkbox.short_description = mark_safe('<label style="margin-left:11px">#</label>')

    def get_permissions(self, obj):
        html = '<ul class="list-unstyled">'
        for v in obj.permissions.all():
            html += '<li>%s | %s | %s</li>' % (capfirst(v.content_type.app_label), capfirst(_(v.content_type.model)), _(v.name))
        html += '</ul>'
        return mark_safe(html)

    get_permissions.short_description = _('Permissions')
    get_permissions.admin_order_field = '-name'

    def get_name_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:%s_%s_change' % (self.opts.app_label, self.opts.model_name), args=(obj.pk,))
        html = u'<a href="%s" class="text-semibold btn-link add-tooltip" data-toggle="tooltip" data-original-title="%s %s %s">%s</a>' % (url, _('Change'), self.opts.verbose_name, obj.name, obj.name)
        return mark_safe(html)

    get_name_link.short_description = _('Name')
    get_name_link.admin_order_field = '-name'


admin.site.unregister(User)
admin.site.unregister(Group)

AuthConfig.verbose_name = (_('Authorization'))

nifty_site.register(MyGroup, MyGroupAdmin)
nifty_site.register(MyUser, MyUserAdmin)
