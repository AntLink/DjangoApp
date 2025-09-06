from .modeladmin import Admin
from django.utils.safestring import mark_safe
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

class LogEntryAdmin(Admin):
    list_per_page = 10
    # date_hierarchy = 'action_time'
    list_filter = [
        'action_time',
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display = [
        'action_time',
        'user',
        'get_content_type',
        'action_flag_',
        'get_change_fields',
    ]

    def log_deletion(self, request, object, object_repr):
        return False

    def has_add_permission(self, request):
        return False

    # def has_change_permission(self, request, obj=None):
    #     return request.user.is_superuser and request.method != 'POST'
    #
    # def has_delete_permission(self, request, obj=None):
    #     return request.user.is_superuser and request.method != 'POST'

    def action_flag_(self, obj):
        flags = {
            1: u'<span class="label label-table label-info">%s</span>' % _('Created'),
            2: u'<span class="label label-table label-success">%s</span>' % _('Updated'),
            3: u'<span class="label label-table label-danger">%s</span>' % _('Deleted'),
        }
        return mark_safe(flags[obj.action_flag])

    action_flag_.admin_order_field = 'action_flag'

    def get_content_type(self, obj):
        return obj.content_type

    get_content_type.admin_order_field = 'content_type'
    get_content_type.short_description = _('Model')

    def get_change_fields(self, obj):
        import json
        from django.utils.text import capfirst
        from django.utils.translation import gettext
        if json.loads(obj.change_message):
            data = json.loads(obj.change_message)[0]
            html = '<ul class="list-unstyled">'
            for v in data['fields']:
                key = str(v)
                rp = str(key.replace('_', ' '))
                new_key = str(capfirst(rp))
                if v == 'password':
                    field = None
                else:
                    field = str(data['fields'][v])
                html += '<li>%s : %s</li>' % (gettext(new_key), Truncator(field).words(5))
            html += '</ul>'

            return mark_safe(html)

    get_change_fields.admin_order_field = 'change_message'
    get_change_fields.short_description = _('Field Changed')

    def get_action_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:%s_%s_change' % (self.opts.app_label, self.opts.model_name), args=(obj.pk,))
        date = u'%s' % obj.action_time.strftime("%b, %d %Y %H:%M %p")
        html = '<a href="%s" class="text-semibold btn-link add-tooltip" data-toggle="tooltip" data-original-title="%s %s">%s</a>' % (url, _('Change'), self.opts.verbose_name, date)
        return mark_safe(html)

    get_action_link.admin_order_field = 'action_time'
    get_action_link.short_description = _('Action time')

    def object_link(self, obj):
        ct = obj.content_type
        return 'admin:%s_%s_change' % (ct.app_label, ct.model)
        # if obj.action_flag == DELETION:
        #     link = escape(obj.object_repr)
        # else:
        #     ct = obj.content_type
        #     link = u'<a href="%s">%s</a>' % (
        #         reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
        #         escape(obj.object_repr),
        #     )
        # return mark_safe(link)

    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'
