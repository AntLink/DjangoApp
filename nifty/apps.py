from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _



class NiftyConfig(AppConfig):
    name = 'nifty'
    verbose_name = _("Settings")
    verbose_name_plural = _("Nifty")
    default_auto_field = 'django.db.models.AutoField'