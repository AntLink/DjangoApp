from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry

class LogEntrys(LogEntry):
    icon_model = 'demo-pli-gear'
    class Meta:
        proxy = True
        app_label = 'nifty'
        verbose_name = _('log entry')
        verbose_name_plural = _('log entry')


class Setting(models.Model):
    icon_model = 'demo-pli-gear'
    user = models.ForeignKey(User, verbose_name=_('Author'), blank=True, null=True, default=1, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    content = models.TextField(default='Content', null=True)
    type = models.CharField(max_length=255, blank=True, default='general')
    autoload = models.CharField(max_length=3, blank=True, default='yes')

    class Meta:
        verbose_name = _('setting')
        db_table = 'ant_setting'
        app_label = 'nifty'
        permissions = (
            ('get_theme_ajax_setting', _('Can get theme settings (ajax)')),
            ('change_theme_ajax_setting', _('Can change theme settings (ajax)')),
            ('user_password_change', _('Can change user password')),
            ('profile_change', _('Can change user profile')),
            ('theme_setting', _('Can change user admin theme setting')),
            ('index_view', _('Can view home index')),
        )

    def __str__(self):
        return self.name


class Admin(Setting):
    icon_model = 'demo-pli-gear'
    class Meta:
        proxy = True
        app_label = 'nifty'
        verbose_name = _('admin setting')
        verbose_name_plural = _('admin setting')


class Site(Setting):
    icon_model = 'demo-pli-gear'
    class Meta:
        proxy = True
        app_label = 'nifty'
        verbose_name = _('site setting')
        verbose_name_plural = _('site setting')
