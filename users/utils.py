import re
from django.core.exceptions import ViewDoesNotExist
from django.urls import path
from nifty.views import nifty_site

named_group_matcher = re.compile(r'\(\?P(<\w+>)')
unnamed_group_matcher = re.compile(r'\(')

def replace_named_groups(pattern):
    r"""
    Find named groups in `pattern` and replace them with the group name. E.g.,
    1. ^(?P<a>\w+)/b/(\w+)$ ==> ^<a>/b/(\w+)$
    2. ^(?P<a>\w+)/b/(?P<c>\w+)/$ ==> ^<a>/b/<c>/$
    """
    named_group_indices = [
        (m.start(0), m.end(0), m.group(1))
        for m in named_group_matcher.finditer(pattern)
    ]
    # Tuples of (named capture group pattern, group name).
    group_pattern_and_name = []
    # Loop over the groups and their start and end indices.
    for start, end, group_name in named_group_indices:
        # Handle nested parentheses, e.g. '^(?P<a>(x|y))/b'.
        unmatched_open_brackets, prev_char = 1, None
        for idx, val in enumerate(list(pattern[end:])):
            # If brackets are balanced, the end of the string for the current
            # named capture group pattern has been reached.
            if unmatched_open_brackets == 0:
                group_pattern_and_name.append((pattern[start:end + idx], group_name))
                break

            # Check for unescaped `(` and `)`. They mark the start and end of a
            # nested group.
            if val == '(' and prev_char != '\\':
                unmatched_open_brackets += 1
            elif val == ')' and prev_char != '\\':
                unmatched_open_brackets -= 1
            prev_char = val

    # Replace the string for named capture groups with their group names.
    for group_pattern, group_name in group_pattern_and_name:
        pattern = pattern.replace(group_pattern, group_name)
    return pattern

def replace_unnamed_groups(pattern):
    r"""
    Find unnamed groups in `pattern` and replace them with '<var>'. E.g.,
    1. ^(?P<a>\w+)/b/(\w+)$ ==> ^(?P<a>\w+)/b/<var>$
    2. ^(?P<a>\w+)/b/((x|y)\w+)$ ==> ^(?P<a>\w+)/b/<var>$
    """
    unnamed_group_indices = [m.start(0) for m in unnamed_group_matcher.finditer(pattern)]
    # Indices of the start of unnamed capture groups.
    group_indices = []
    # Loop over the start indices of the groups.
    for start in unnamed_group_indices:
        # Handle nested parentheses, e.g. '^b/((x|y)\w+)$'.
        unmatched_open_brackets, prev_char = 1, None
        for idx, val in enumerate(list(pattern[start + 1:])):
            if unmatched_open_brackets == 0:
                group_indices.append((start, start + 1 + idx))
                break

            # Check for unescaped `(` and `)`. They mark the start and end of
            # a nested group.
            if val == '(' and prev_char != '\\':
                unmatched_open_brackets += 1
            elif val == ')' and prev_char != '\\':
                unmatched_open_brackets -= 1
            prev_char = val

    # Remove unnamed group matches inside other unnamed capture groups.
    group_start_end_indices = []
    prev_end = None
    for start, end in group_indices:
        if prev_end and start > prev_end or not prev_end:
            group_start_end_indices.append((start, end))
        prev_end = end

    if group_start_end_indices:
        # Replace unnamed groups with <var>. Handle the fact that replacing the
        # string between indices will change string length and thus indices
        # will point to the wrong substring if not corrected.
        final_pattern, prev_end = [], None
        for start, end in group_start_end_indices:
            if prev_end:
                final_pattern.append(pattern[prev_end:start])
            final_pattern.append(pattern[:start] + '<var>')
            prev_end = end
        final_pattern.append(pattern[prev_end:])
        return ''.join(final_pattern)
    else:
        return pattern

def extract_views_from_urlpatterns(urlpatterns, base='', namespace=None):
    """
    Return a list of views from a list of urlpatterns.

    Each object in the returned list is a two-tuple: (view_func, regex)
    """
    views = []
    for p in urlpatterns:
        if hasattr(p, 'url_patterns'):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            views.extend(extract_views_from_urlpatterns(
                patterns,
                base + str(p.pattern),
                (namespace or []) + (p.namespace and [p.namespace] or [])
            ))
        elif hasattr(p, 'callback'):
            try:
                views.append((p.callback, base + str(p.pattern), namespace, p.name))
            except ViewDoesNotExist:
                continue
        else:
            raise TypeError(_("%s does not appear to be a urlpattern object") % p)
    return views


def get_view_name(view_func):
    mod_name = view_func.__module__
    view_name = getattr(view_func, '__qualname__', view_func.__class__.__name__)
    return mod_name + '.' + view_name


def simplify_regex(pattern):
    r"""
    Clean up urlpattern regexes into something more readable by humans. For
    example, turn "^(?P<sport_slug>\w+)/athletes/(?P<athlete_slug>\w+)/$"
    into "/<sport_slug>/athletes/<athlete_slug>/".
    """
    pattern = replace_named_groups(pattern)
    pattern = replace_unnamed_groups(pattern)
    # clean up any outstanding regex-y characters.
    pattern = pattern.replace('^', '').replace('$', '').replace('?', '')
    if not pattern.startswith('/'):
        pattern = '/' + pattern
    return pattern


def get_url_choice():
    from django.contrib import admin
    views = []
    seen = set()

    urlconf = [
        path('', nifty_site.urls),
        path('', admin.site.urls),
    ]
    # urlconfs = import_module(settings.ROOT_URLCONF)
    view_functions = extract_views_from_urlpatterns(urlconf)
    # view_functions = extract_views_from_urlpatterns(urlconf.urlpatterns)
    for (func, regex, namespace, name) in view_functions:
        # namespace = ':'.join((namespace or []))
        # names = name
        # full_name = get_view_name(func)
        url = simplify_regex(regex)
        url_name = ':'.join((namespace or []) + (name and [name] or []))
        reg = re.compile("((object_id)|(app_label)|(<id>)|(jsi18n)|(ajax)|(add)|(login)|(logout)|(autocomplete)|(done)|(view)|(password_change)|(mode)|(upload)|(tax)|(perpage))")
        if not reg.findall(url):
            views.append([url_name, url])
    views.sort()


    no_dups = []
    for lst in views:

        # convert to hashable type
        current = tuple(lst)

        # If element not in seen, add it to both
        if current not in seen:
            no_dups.append(lst)
            seen.add(current)

    return no_dups


def get_menu(context, request):
    from nifty.templatetags.suit_menu import get_admin_site, Menu
    """
    :type request: HttpRequest
    """
    if not isinstance(request, HttpRequest):
        return None

    # Try to get app list
    if hasattr(request, 'current_app'):
        # Django 1.8 uses request.current_app instead of context.current_app
        template_response = get_admin_site(request.current_app).app_index_for_menu(request)
    else:
        try:
            template_response = get_admin_site(context.current_app).app_index_for_menu(request)
        # Django 1.10 removed the current_app parameter for some classes and functions.
        # Check the release notes.
        except AttributeError:
            template_response = get_admin_site(context.request.resolver_match.namespace).index(request)

    try:
        app_list = template_response.context_data['app_list']
    except Exception:
        return
    return Menu(context, request, app_list).get_app_list()