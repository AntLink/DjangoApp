from django.contrib.admin import ModelAdmin
from django.conf import settings


def default_config():
    return settings.NIFTY_SETTING


def get_config(param=None):
    config_key = 'SUIT_CONFIG'
    if hasattr(settings, config_key):
        config = getattr(settings, config_key, {})
    else:
        config = default_config()
    if param:
        value = config.get(param)
        if value is None:
            value = default_config().get(param)
        return value
    return config


# Reverse default actions position
ModelAdmin.actions_on_top = False
ModelAdmin.actions_on_bottom = True

# Set global list_per_page
ModelAdmin.list_per_page = get_config('LIST_PER_PAGE')



def setup_filer():
    from nifty.widgets import AutosizedTextarea
    from filer.admin.imageadmin import ImageAdminForm
    from filer.admin.fileadmin import FileAdminChangeFrom
    from filer.admin import FolderAdmin

    def ensure_meta_widgets(meta_cls):
        if not hasattr(meta_cls, 'widgets'):
            meta_cls.widgets = {}

        meta_cls.widgets['description'] = AutosizedTextarea

    ensure_meta_widgets(ImageAdminForm.Meta)
    ensure_meta_widgets(FileAdminChangeFrom.Meta)
    FolderAdmin.actions_on_top = False
    FolderAdmin.actions_on_bottom = True


if 'filer' in settings.INSTALLED_APPS:
    setup_filer()
