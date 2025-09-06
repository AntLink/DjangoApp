from .forms import ActionForm
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.encoding import force_str
from django.contrib.admin import helpers
from .views import nifty_site
import datetime, json


def date_default(o):
    if type(o) is datetime.date or type(o) is datetime.datetime:
        return o.isoformat()


def AdminCreate(modeladmin, model, name=None, vname='Verbose Name', vnamep='Verbose Name Plural'):
    class Meta:
        proxy = True
        app_label = model._meta.app_label
        verbose_name = vname
        verbose_name_plural = vnamep

    attrs = {'__module__': '', 'Meta': Meta}
    newmodel = type(name, (model,), attrs)

    nifty_site.register(newmodel, modeladmin)
    return modeladmin


class Admin(admin.ModelAdmin):
    def __init__(self, model, admin_site):
        super(Admin, self).__init__(model, admin_site)

    action_form = ActionForm

    # @property
    # def media(self):
    #     from django import forms
    #     from django.conf import settings
    #     extra = '' if settings.DEBUG else '.min'
    #     js = [
    #         'core.js',
    #         'admin/RelatedObjectLookups.js',
    #         # 'actions%s.js' % extra,
    #         # 'urlify.js',
    #         # 'prepopulate%s.js' % extra,
    #         # 'vendor/xregexp/xregexp%s.js' % extra,
    #         # '../../nifty/js/suit.init.js',
    #         # '../../nifty/js/suit.js',
    #     ]
    #     return forms.Media(js=['admin/js/%s' % url for url in js])

    def construct_change_message(self, request, form, formsets, add=False):
        from .utils import change_log_message
        return change_log_message(form, formsets, add, request)

    def log_deletion(self, request, object, object_repr):
        """
        Log that an object will be deleted. Note that this method must be
        called before the deletion.

        The default implementation creates an admin LogEntry object.
        """
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
        return super(Admin, self).get_action_choices(request, default_choices)

    def action_checkbox(self, obj):
        from django import forms
        checkbox = forms.CheckboxInput({'class': 'magic-checkbox', 'id': 'list-%s' % obj.id}, lambda value: False)
        html = u'%s<label for="list-%s" style="margin-left:7px"></label>' % (checkbox.render(helpers.ACTION_CHECKBOX_NAME, force_str(obj.pk)), obj.pk)
        return mark_safe(html)

    action_checkbox.short_description = mark_safe('<label style="margin-left:11px">#</label>')
