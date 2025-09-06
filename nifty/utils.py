from django import VERSION
from django.utils.translation import override as translation_override


def django_major_version():
    return VERSION[:2]


def value_by_version(args):
    """
    Return value by version
    Return latest value if version not found
    """
    version_map = args_to_dict(args)
    major_version = '.'.join(str(v) for v in django_major_version())
    return version_map.get(major_version,
                           list(version_map.values())[-1])


def args_to_dict(args):
    """
    Convert template tag args to dict
    Format {% suit_bc 1.5 'x' 1.6 'y' %} to { '1.5': 'x', '1.6': 'y' }
    """
    return dict(zip(args[0::2], args[1::2]))


def change_log_message(form, formsets, add, request):
    """
    Construct a JSON structure describing changes from a changed object.
    Translations are deactivated so that strings are stored untranslated.
    Translation happens later on LogEntry access.
    """
    change_message = []
    data = {}

    for v in form.changed_data:
        data.update({v: request.POST.get(v)})

    if add:
        change_message.append({
            'action': 'Created',
            'fields': data
        })
    elif form.changed_data:
        change_message.append({
            'action': 'Updated',
            'fields': data
        })

    if formsets:
        with translation_override(None):
            for formset in formsets:
                for added_object in formset.new_objects:
                    change_message.append({
                        'added': {
                            'name': str(added_object._meta.verbose_name),
                            'object': str(added_object),
                        }
                    })
                for changed_object, changed_fields in formset.changed_objects:
                    change_message.append({
                        'changed': {
                            'name': str(changed_object._meta.verbose_name),
                            'object': str(changed_object),
                            'fields': changed_fields,
                        }
                    })
                for deleted_object in formset.deleted_objects:
                    change_message.append({
                        'deleted': {
                            'name': str(deleted_object._meta.verbose_name),
                            'object': str(deleted_object),
                        }
                    })
    return change_message
