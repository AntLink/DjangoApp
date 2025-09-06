from copy import copy
import types, datetime
from django.utils.html import format_html

from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.utils.translation import gettext_lazy as _
from django.db import models
from inspect import getfullargspec
from django import template
from django.template.loader import get_template
from django.utils.safestring import mark_safe

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.utils import (
    display_for_field, display_for_value, label_for_field, lookup_field,
)
from django.contrib.admin.templatetags.admin_list import result_headers, result_hidden_fields, _coerce_field_name
from django.contrib.admin.views.main import ALL_VAR, PAGE_VAR
from django.utils.html import escape, conditional_escape

tpl_context_class = dict


try:
    # Python 3.
    from urllib.parse import parse_qs
except ImportError:
    # Python 2.5+
    from urlparse import urlparse

    try:
        # Python 2.6+
        from urlparse import parse_qs
    except ImportError:
        # Python <=2.5
        from cgi import parse_qs

register = template.Library()

DOT = '.'


@register.simple_tag
def paginator_number(cl, i):
    """
    Generates an individual page index link in a paginated list.
    """
    if i == DOT:
        return mark_safe(
            '<li class="disabled"><a href="#" onclick="return false;">..'
            '.</a></li>')
    elif i == cl.page_num:
        return mark_safe(
            '<li class="active"><a href="">%d</a></li> ' % (i + 1))
    else:
        return mark_safe('<li><a href="%s"%s>%d</a></li> ' % (
            escape(cl.get_query_string({PAGE_VAR: i})),
            (i == cl.paginator.num_pages - 1 and ' class="end"' or ''),
            i + 1))


@register.simple_tag
def paginator_info(cl):
    paginator = cl.paginator

    # If we show all rows of list (without pagination)
    if cl.show_all and cl.can_show_all:
        entries_from = 1 if paginator.count > 0 else 0
        entries_to = paginator.count
    else:
        entries_from = (
                (paginator.per_page * cl.page_num) + 1) if paginator.count > 0 else 0
        entries_to = entries_from - 1 + paginator.per_page
        if paginator.count < entries_to:
            entries_to = paginator.count

    return '%s - %s' % (entries_from, entries_to)


@register.simple_tag
def page(cl, num):
    from django.core.paginator import EmptyPage
    paginator = cl.paginator
    d = int(num)
    try:
        page = paginator.page(d)
    except EmptyPage:
        page = paginator.page(1)
    return page


@register.simple_tag
def pagemin(page):
    num = (page - 1)
    return num


@register.simple_tag
def get_request(request, name):
    return request.GET.get(name, False)


@register.simple_tag
def post_request(request, name):
    return request.POST.get(name, False)


@register.inclusion_tag('admin/pagination.html')
def pagination(cl):
    """
    Generates the series of links to the pages in a paginated list.
    """
    paginator, page_num = cl.paginator, cl.page_num

    pagination_required = (not cl.show_all or not cl.can_show_all) \
                          and cl.multi_page
    if not pagination_required:
        page_range = []
    else:
        ON_EACH_SIDE = 3
        ON_ENDS = 2

        # If there are 10 or fewer pages, display links to every page.
        # Otherwise, do some fancy
        if paginator.num_pages <= 8:
            page_range = range(paginator.num_pages)
        else:
            # Insert "smart" pagination links, so that there are always ON_ENDS
            # links at either end of the list of pages, and there are always
            # ON_EACH_SIDE links at either end of the "current page" link.
            page_range = []
            if page_num > (ON_EACH_SIDE + ON_ENDS):
                page_range.extend(range(0, ON_EACH_SIDE - 1))
                page_range.append(DOT)
                page_range.extend(range(page_num - ON_EACH_SIDE, page_num + 1))
            else:
                page_range.extend(range(0, page_num + 1))
            if page_num < (paginator.num_pages - ON_EACH_SIDE - ON_ENDS - 1):
                page_range.extend(
                    range(page_num + 1, page_num + ON_EACH_SIDE + 1))
                page_range.append(DOT)
                page_range.extend(
                    range(paginator.num_pages - ON_ENDS, paginator.num_pages))
            else:
                page_range.extend(range(page_num + 1, paginator.num_pages))

    need_show_all_link = cl.can_show_all and not cl.show_all and cl.multi_page
    return {
        'cl': cl,
        'pagination_required': pagination_required,
        'show_all_url': need_show_all_link and cl.get_query_string(
            {ALL_VAR: ''}),
        'page_range': page_range,
        'ALL_VAR': ALL_VAR,
        '1': 1,
    }


@register.simple_tag
def suit_list_filter_select(cl, spec):
    tpl = get_template(spec.template)
    choices = list(spec.choices(cl))
    field_key = spec.field_path if hasattr(spec, 'field_path') else \
        spec.parameter_name
    matched_key = field_key
    for choice in choices:
        query_string = choice['query_string'][1:]
        query_parts = parse_qs(query_string)

        value = ''
        matches = {}
        for key in query_parts.keys():
            if key == field_key:
                value = query_parts[key][0]
                matched_key = key
            elif key.startswith(
                    field_key + '__') or '__' + field_key + '__' in key:
                value = query_parts[key][0]
                matched_key = key

            if value:
                matches[matched_key] = value

        # Iterate matches, use first as actual values, additional for hidden
        i = 0
        for key, value in matches.items():
            if i == 0:
                choice['name'] = key
                choice['val'] = value
            else:
                choice['additional'] = '%s=%s' % (key, value)
            i += 1

    return tpl.render(tpl_context_class({
        'field_name': field_key,
        'title': spec.title,
        'choices': choices,
        'spec': spec,
    }))


@register.filter
def headers_handler(result_headers, cl):
    """
    Adds field name to css class, so we can style specific columns
    """
    # field = cl.list_display.get()
    attrib_key = 'class_attrib'
    for i, header in enumerate(result_headers):
        field_name = cl.list_display[i]
        if field_name == 'action_checkbox':
            continue
        if not attrib_key in header:
            header[attrib_key] = mark_safe(' class=""')

        pattern = 'class="'
        if pattern in header[attrib_key]:
            replacement = '%s%s-column ' % (pattern, field_name)
            header[attrib_key] = mark_safe(
                header[attrib_key].replace(pattern, replacement))

    return result_headers


def dict_to_attrs(attrs):
    return mark_safe(' ' + ' '.join(['%s="%s"' % (k, v)
                                     for k, v in attrs.items()]))


def nifty_result_headers(cl):
    """
    Generate the list column headers.
    """
    ordering_field_columns = cl.get_ordering_field_columns()
    for i, field_name in enumerate(cl.list_display):
        text, attr = label_for_field(
            field_name, cl.model,
            model_admin=cl.model_admin,
            return_attr=True
        )
        is_field_sortable = cl.sortable_by is None or field_name in cl.sortable_by
        if attr:
            field_name = _coerce_field_name(field_name, i)
            # Potentially not sortable

            # if the field is the action checkbox: no sorting and special class
            if field_name == 'action_checkbox':
                yield {
                    "text": text,
                    "class_attrib": mark_safe(' class="action-checkbox-column"'),
                    "sortable": False,
                }
                continue

            admin_order_field = getattr(attr, "admin_order_field", None)
            if not admin_order_field:
                is_field_sortable = False

        if not is_field_sortable:
            # Not sortable
            yield {
                'text': text,
                'class_attrib': format_html(' class="column-{}"', field_name),
                'sortable': False,
            }
            continue

        # OK, it is sortable if we got this far
        th_classes = ['sortable', 'column-{}'.format(field_name)]
        order_type = ''
        new_order_type = 'asc'
        sort_priority = 0
        # Is it currently being sorted on?
        is_sorted = i in ordering_field_columns
        if is_sorted:
            order_type = ordering_field_columns.get(i).lower()
            sort_priority = list(ordering_field_columns).index(i) + 1
            th_classes.append('sorted %sending' % order_type)
            new_order_type = {'asc': 'desc', 'desc': 'asc'}[order_type]

        # build new ordering param
        o_list_primary = []  # URL for making this field the primary sort
        o_list_remove = []  # URL for removing this field from sort
        o_list_toggle = []  # URL for toggling order type for this field

        def make_qs_param(t, n):
            return ('-' if t == 'desc' else '') + str(n)

        for j, ot in ordering_field_columns.items():
            if j == i:  # Same column
                param = make_qs_param(new_order_type, j)
                # We want clicking on this header to bring the ordering to the
                # front
                o_list_primary.insert(0, param)
                o_list_toggle.append(param)
                # o_list_remove - omit
            else:
                param = make_qs_param(ot, j)
                o_list_primary.append(param)
                o_list_toggle.append(param)
                o_list_remove.append(param)

        if i not in ordering_field_columns:
            o_list_primary.insert(0, make_qs_param(new_order_type, i))

        yield {
            "text": text,
            "sortable": True,
            "sorted": is_sorted,
            "ascending": order_type == "asc",
            "sort_priority": sort_priority,
            "url_primary": cl.get_query_string({ORDER_VAR: '.'.join(o_list_primary)}),
            "url_remove": cl.get_query_string({ORDER_VAR: '.'.join(o_list_remove)}),
            "url_toggle": cl.get_query_string({ORDER_VAR: '.'.join(o_list_toggle)}),
            "class_attrib": format_html(' class="{}"', ' '.join(th_classes)) if th_classes else '',
        }


def items_for_result(cl, result, form):
    """
    Generate the actual list of data.
    """

    def link_in_col(is_first, field_name, cl):
        if cl.list_display_links is None:
            return False
        if is_first and not cl.list_display_links:
            return True
        return field_name in cl.list_display_links

    first = True
    pk = cl.lookup_opts.pk.attname
    for field_index, field_name in enumerate(cl.list_display):
        empty_value_display = cl.model_admin.get_empty_value_display()
        row_classes = ['field-%s' % _coerce_field_name(field_name, field_index)]
        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except ObjectDoesNotExist:
            result_repr = empty_value_display
        else:
            empty_value_display = getattr(attr, 'empty_value_display', empty_value_display)
            if f is None or f.auto_created:
                if field_name == 'action_checkbox':
                    row_classes = ['action-checkbox']
                boolean = getattr(attr, 'boolean', False)
                result_repr = display_for_value(value, empty_value_display, boolean)
                if isinstance(value, (datetime.date, datetime.time)):
                    row_classes.append('nowrap')
            else:
                if isinstance(f.remote_field, models.ManyToOneRel):
                    field_val = getattr(result, f.name)
                    if field_val is None:
                        result_repr = empty_value_display
                    else:
                        result_repr = field_val
                else:
                    result_repr = display_for_field(value, f, empty_value_display)
                if isinstance(f, (models.DateField, models.TimeField, models.ForeignKey)):
                    row_classes.append('nowrap')
        if str(result_repr) == '':
            result_repr = mark_safe('&nbsp;')
        row_class = mark_safe(' class="%s"' % ' '.join(row_classes))
        # If list_display_links not defined, add the link tag to the first field
        if link_in_col(first, field_name, cl):
            table_tag = 'td' if first else 'td'
            first = False

            # Display link to the result's change_view if the url exists, else
            # display just the result's representation.
            try:
                url = cl.url_for_result(result)
            except NoReverseMatch:
                link_or_text = result_repr
            else:
                url = add_preserved_filters({'preserved_filters': cl.preserved_filters, 'opts': cl.opts}, url)
                # Convert the pk to something that can be used in Javascript.
                # Problem cases are non-ASCII strings.
                if cl.to_field:
                    attr = str(cl.to_field)
                else:
                    attr = pk
                value = result.serializable_value(attr)
                tooltip_title = u'%s %s' % (_('Change'), cl.opts.verbose_name)
                link_or_text = format_html(
                    '<a class="text-semibold btn-link add-tooltip" data-original-title="{}" href="{}"{}>{}</a>',
                    tooltip_title,
                    url,
                    format_html(
                        ' data-popup-opener="{}"', value
                    ) if cl.is_popup else '',
                    result_repr)

            yield format_html('<{}{}>{}</{}>',
                              table_tag,
                              row_class,
                              link_or_text,
                              table_tag)
        else:
            # By default the fields come from ModelAdmin.list_editable, but if we pull
            # the fields out of the form instead of list_editable custom admins
            # can provide fields on a per request basis
            if (form and field_name in form.fields and not (
                    field_name == cl.model._meta.pk.name and
                    form[cl.model._meta.pk.name].is_hidden)):
                bf = form[field_name]
                result_repr = mark_safe(str(bf.errors) + str(bf))
            yield format_html('<td{}>{}</td>', row_class, result_repr)
    if form and not form[cl.model._meta.pk.name].is_hidden:
        yield format_html('<td>{}</td>', form[cl.model._meta.pk.name])


class ResultList(list):
    """
    Wrapper class used to return items in a list_editable changelist, annotated
    with the form object for error reporting purposes. Needed to maintain
    backwards compatibility with existing admin templates.
    """

    def __init__(self, form, *items):
        self.form = form
        super().__init__(*items)


def results(cl):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            yield ResultList(form, items_for_result(cl, res, form))
    else:
        for res in cl.result_list:
            yield ResultList(None, items_for_result(cl, res, None))


def nifty_result_list(cl):
    """
    Display the headers and data list together.
    """
    headers = list(result_headers(cl))
    num_sorted_fields = 0
    for h in headers:
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1
    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': headers,
            'num_sorted_fields': num_sorted_fields,
            'results': list(results(cl))}


@register.inclusion_tag('admin/change_list_results.html', takes_context=True)
def result_list_with_context(context, cl):
    """
    Wraps Djangos default result_list to ammend the context with the request.

    This gives us access to the request in change_list_results.
    """
    res = nifty_result_list(cl)
    res['request'] = context['request']
    return res


@register.simple_tag(takes_context=True)
def result_row_attrs(context, cl, row_index):
    """
    Returns row attributes based on object instance
    """
    row_index -= 1
    attrs = {
        'class': 'row1' if row_index % 2 == 0 else 'row2'
    }
    suit_row_attributes = getattr(cl.model_admin, 'suit_row_attributes', None)
    if not suit_row_attributes:
        return dict_to_attrs(attrs)

    instance = cl.result_list[row_index]

    # Backwards compatibility for suit_row_attributes without request argument
    args = getfullargspec(suit_row_attributes)
    if 'request' in args[0]:
        new_attrs = suit_row_attributes(instance, context['request'])
    else:
        new_attrs = suit_row_attributes(instance)

    if not new_attrs:
        return dict_to_attrs(attrs)

    # Validate
    if not isinstance(new_attrs, dict):
        raise TypeError('"suit_row_attributes" must return dict. Got: %s: %s' %
                        (new_attrs.__class__.__name__, new_attrs))

    # Merge 'class' attribute
    if 'class' in new_attrs:
        attrs['class'] += ' ' + new_attrs.pop('class')

    attrs.update(new_attrs)
    return dict_to_attrs(attrs)


@register.filter
def cells_handler(results, cl):
    """
    Changes result cell attributes based on object instance and field name
    """
    suit_cell_attributes = getattr(cl.model_admin, 'suit_cell_attributes', None)
    if not suit_cell_attributes:
        return results

    class_pattern = 'class="'
    td_pattern = '<td'
    th_pattern = '<th'
    for row, result in enumerate(results):
        instance = cl.result_list[row]
        for col, item in enumerate(result):
            field_name = cl.list_display[col]
            attrs = copy(suit_cell_attributes(instance, field_name))
            if not attrs:
                continue

            # Validate
            if not isinstance(attrs, dict):
                raise TypeError('"suit_cell_attributes" must return dict. '
                                'Got: %s: %s' % (
                                    attrs.__class__.__name__, attrs))

            # Merge 'class' attribute
            if class_pattern in item.split('>')[0] and 'class' in attrs:
                css_class = attrs.pop('class')
                replacement = '%s%s ' % (class_pattern, css_class)
                result[col] = mark_safe(
                    item.replace(class_pattern, replacement))

            # Add rest of attributes if any left
            if attrs:
                cell_pattern = td_pattern if item.startswith(
                    td_pattern) else th_pattern

                result[col] = mark_safe(
                    result[col].replace(cell_pattern,
                                        td_pattern + dict_to_attrs(attrs)))

    return results


@register.inclusion_tag('admin/searchbox_form.html')
def searchbox_form(cl):
    """
    Displays a search form for searching the list.
    """
    return {
        'cl': cl,
        'show_result_count': cl.result_count != cl.full_result_count,
        'search_var': 'q'
    }


@register.filter(is_safe=True, needs_autoescape=True)
def unify_unordered_list(value, autoescape=True):
    """
    Recursively take a self-nested list and return an HTML unordered list --
    WITHOUT opening and closing <ul> tags.

    Assume the list is in the proper format. For example, if ``var`` contains:
    ``['States', ['Kansas', ['Lawrence', 'Topeka'], 'Illinois']]``, then
    ``{{ var|unordered_list }}`` returns::

        <li>States
        <ul>
                <li>Kansas
                <ul>
                        <li>Lawrence</li>
                        <li>Topeka</li>
                </ul>
                </li>
                <li>Illinois</li>
        </ul>
        </li>
    """
    if autoescape:
        escaper = conditional_escape
    else:
        def escaper(x):
            return x

    def walk_items(item_list):
        item_iterator = iter(item_list)
        try:
            item = next(item_iterator)
            while True:
                try:
                    next_item = next(item_iterator)
                except StopIteration:
                    yield item, None
                    break
                if isinstance(next_item, (list, tuple, types.GeneratorType)):
                    try:
                        iter(next_item)
                    except TypeError:
                        pass
                    else:
                        yield item, next_item
                        item = next(item_iterator)
                        continue
                yield item, None
                item = next_item
        except StopIteration:
            pass

    def list_formatter(item_list, tabs=1):
        indent = '\t' * tabs
        output = []
        for item, children in walk_items(item_list):
            sublist = ''
            if children:
                sublist = '\n%s<ul class="list-unstyled mar-btm">\n%s\n%s</ul><hr>\n%s' % (
                    indent, list_formatter(children, tabs + 1), indent, indent)
            output.append('%s<li>%s%s</li>' % (
                indent, escaper(item), sublist))
        return '\n'.join(output)

    return mark_safe(list_formatter(value))
