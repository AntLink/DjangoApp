from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

def remove_profile_permissions(apps, schema_editor):
    """Reverse the above additions of permissions."""
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    content_type = ContentType.objects.get(
        model='profile',
        app_label='users',
    )
    # This cascades to Group
    Permission.objects.filter(
        content_type=content_type,
        codename__in=('add_profile', 'change_profile', 'delete_profile','view_profile'),
    ).delete()


def add_myuser_proxy_permissions(apps, schema_editor):
    app_config = apps.get_app_config('users')
    model = app_config.get_model('User')
    opts = model._meta
    ctype, created = ContentType.objects.get_or_create(
        app_label=opts.app_label,
        model=opts.object_name.lower(),
    )

    for codename, name in _get_all_permissions(opts):
        p, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=ctype,
            defaults={'name': f'{name} (Proxy)'})
        if created:
            print(f'Adding permission: {p}')


def add_mygroup_proxy_permissions(apps, schema_editor):
    app_config = apps.get_app_config('users')
    model = app_config.get_model('Group')
    opts = model._meta
    ctype, created = ContentType.objects.get_or_create(
        app_label=opts.app_label,
        model=opts.object_name.lower(),
    )

    for codename, name in _get_all_permissions(opts):
        p, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=ctype,
            defaults={'name': f'{name} (Proxy)'})
        if created:
            print(f'Adding permission: {p}')
