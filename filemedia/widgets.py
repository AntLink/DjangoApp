import json
from django import forms
from django.utils.encoding import force_str as force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.urls import reverse

class FileMediaSingleFile(forms.HiddenInput):
    template_name = 'admin/widgets/singlefile.html'
    def __init__(self, attrs=None):
        defaults = {'style': 'position:absolut;'}
        new_attrs = _make_attrs(attrs, defaults, "dropzone")
        super(FileMediaSingleFile, self).__init__(attrs=new_attrs)

    @property
    def options(self):
        options = {}
        options['upload_url'] = reverse('admin:filemedia_file_ajax_uploads')
        return options

    # def get_context(self, name, value, attrs):
    #     super(FileMediaSingleImage,self).get_context(name,value,attrs)

    def render(self, name, value, attrs=None, renderer=None):
        attrs['data-filemedia-options'] = json.dumps(self.options)
        attrs['data-name'] = name
        output = super(FileMediaSingleFile, self).render(name, value, attrs, renderer)
        return mark_safe(output)

    def _media(self):
        js = (
            # 'admin/filemedia/js/dropzone/dropzone.min.js',
            # 'admin/filemedia/js/singlefile.min.js',
            # 'admin/filemedia/js/singlefile.js',
        )
        css = {
            'all': (
                'admin/filemedia/css/singlefile.css',
            )
        }
        return forms.Media(css=css, js=js)

    media = property(_media)

class FileMediaSingleImage(forms.HiddenInput):
    template_name = 'admin/widgets/singleimage.html'
    def __init__(self, attrs=None):
        defaults = {'style': 'position:absolut;'}
        new_attrs = _make_attrs(attrs, defaults, "dropzone")
        super(FileMediaSingleImage, self).__init__(attrs=new_attrs)

    @property
    def options(self):
        options = {}
        options['upload_url'] = reverse('admin:filemedia_image_ajax_uploads')
        return options

    # def get_context(self, name, value, attrs):
    #     super(FileMediaSingleImage,self).get_context(name,value,attrs)

    def render(self, name, value, attrs=None, renderer=None):
        attrs['data-filemedia-options'] = json.dumps(self.options)
        attrs['data-name'] = name
        output = super(FileMediaSingleImage, self).render(name, value, attrs, renderer)
        return mark_safe(output)

    def _media(self):
        js = (
            # 'admin/filemedia/js/dropzone/dropzone.min.js',
            # 'admin/filemedia/js/singleimage.min.js',
            # 'admin/filemedia/js/singleimage.js',
        )
        css = {
            'all': (
                'admin/filemedia/css/singleimage.css',
            )
        }
        return forms.Media(css=css, js=js)

    media = property(_media)

class FileMediaPhoto(forms.HiddenInput):
    template_name = 'admin/widgets/photo.html'

    def __init__(self, attrs=None):
        defaults = {'style': 'width:15%;cursor: pointer;'}
        new_attrs = _make_attrs(attrs, defaults, "img-filemedia img-responsive img-rounded")
        super(FileMediaPhoto, self).__init__(attrs=new_attrs)


    @property
    def options(self):
        options = {}
        options['upload_url'] = reverse('admin:filemedia_image_ajax_uploads')
        options['load_url'] = reverse('admin:filemedia_image_ajax_gets')
        options['update_url'] = reverse('admin:filemedia_image_ajax_change')
        options['delete_url'] = reverse('admin:filemedia_image_ajax_delete')
        return options

    def render(self, name, value, attrs=None, renderer=None):
        attrs['data-filemedia-options'] = json.dumps(self.options)
        output = super(FileMediaPhoto, self).render(name, value, attrs, renderer)
        return mark_safe(output)

    def _media(self):
        js = (
            'admin/filemedia/js/slimscroll/slimscroll.min.js',
            'admin/filemedia/js/freewall/freewall.js',
            'admin/filemedia/js/dropzone/dropzone.min.js',
            # 'admin/filemedia/js/photo.min.js',
            'admin/filemedia/js/photo.js',
        )
        css = {
            'all': (
                'admin/filemedia/js/dropzone/dropzonenew.min.css',
            )
        }
        return forms.Media(css=css, js=js)

    media = property(_media)


class TagFilteredSelectMultiple(FilteredSelectMultiple):
    class Media:
        css = {
            'all': ('nifty/css/forms-select.css',)
        }


class SelfRelationships(forms.ModelMultipleChoiceField): pass


class TreeCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def __init__(self, css_class=None, label_css_style=None, value='pk', label='name', level='level', **kwargs):
        super(TreeCheckboxSelectMultiple, self).__init__(**kwargs)
        self.css_class = css_class
        self.label_css_style = label_css_style
        self.value = value
        self.label = label
        self.level = level

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs)

        output = []
        if self.css_class:
            output.append(u'<ul class="%s">' % self.css_class)
        else:
            output.append(u'<ul>')

        str_values = set([force_unicode(v) for v in value])
        i = 0
        for tax in self.choices.queryset.values(self.value, self.label, self.level):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (
                    attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(tax['%s' % self.value])
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(tax['%s' % self.label]))
            if tax['%s' % self.label] == 0:
                output.append(u'<li>')
            else:
                output.append(u'<li style="margin-left: %spx;">' % (tax['%s' % self.level] * 16))

            output.append(u'<div class="checkbox"><div class="form-checkbox form-normal  form-text" style="%s" %s>%s <span clas="text-muted">%s</div></label></div>' % (self.label_css_style, label_for, rendered_cb, option_label))

        # output.append(u'</li>')
        # output.append(u'</ul>')
        return mark_safe(u'\n'.join(output))


def _make_attrs(attrs, defaults=None, classes=None):
    result = defaults.copy() if defaults else {}
    if attrs:
        result.update(attrs)
    if classes:
        result["class"] = " ".join((classes, result.get("class", "")))
    return result
