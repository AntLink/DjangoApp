from django.apps import AppConfig
# from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext_lazy as _

class UsersConfig(AppConfig):
    name = 'users'
    verbose_name = _("Authorization")
    verbose_name_plural = _("Authorizations")
