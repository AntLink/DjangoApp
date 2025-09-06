from .models import Setting
from django.contrib.admin.models import LogEntry
import datetime


def log_entry_results(request):
    date = datetime.datetime.now()
    gs = {

    }
    if request.user.is_anonymous:
        return gs
    else:
        gs['log_entry_results'] = LogEntry.objects.filter(action_time__date=date.now()).all()[:15]
        return gs


def site(request):
    gs = {}
    for v in Setting.objects.filter(type='site'):
        gs[v.value] = v.content
    return gs


def admin(request):
    gs = {}
    for v in Setting.objects.filter(type='admin'):
        gs[v.value] = v.content
    return gs
    # if request.user.is_anonymous:
    #     return gs
    # else:
    #     for v in Setting.objects.filter(type='admin'):
    #         gs[v.value] = v.content
    #     return gs


def admin_theme(request):
    gs = {}
    if request.user.is_anonymous:
        return gs
    else:
        for v in Setting.objects.filter(type='admin_theme', user=request.user):
            gs[v.value] = v.content
        return gs
