from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class WordConfig(AppConfig):
    name = 'word'
    verbose_name = _("Words")
