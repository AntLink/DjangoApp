from django import forms
# from django.utils.encoding import force_unicode
from django.utils.encoding import force_str as force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import FilteredSelectMultiple


class TitleTextInput(forms.TextInput): pass


class AddressTextInput(forms.TextInput): pass


class UserSelectInput(forms.Select): pass


class LayoutSelectInput(forms.Select): pass


class SidebarInput(forms.CheckboxInput): pass


class TagFilteredSelectMultiple(FilteredSelectMultiple): pass


class ImageGalleryHideInput(forms.HiddenInput): pass


class WordMetaHideInput(forms.HiddenInput): pass


class PriceInput(forms.NumberInput): pass


class StarInput(forms.NumberInput): pass


class LatitudeInput(forms.TextInput): pass


class LongitudeInput(forms.TextInput): pass


class ImageHideInput(forms.HiddenInput): pass


class SelfRelationships(forms.ModelMultipleChoiceField): pass


class TreeCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def __init__(self, css_class=None, label_css_style=None, value='pk', label='name', level='level', **kwargs):
        super(TreeCheckboxSelectMultiple, self).__init__(**kwargs)
        self.css_class = css_class
        self.label_css_style = label_css_style
        self.value = value
        self.label = label
        self.level = level

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        has_id = attrs and 'id' in attrs

        final_attrs = self.build_attrs(attrs)
        final_attrs['name'] = name

        output = []
        if self.css_class:
            output.append(f'<ul class="{self.css_class}">')
        else:
            output.append('<ul>')

        str_values = set([str(v) for v in value])  # pakai str, bukan force_unicode
        i = 0
        for tax in self.choices.queryset.values(self.value, self.label, self.level):
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = f' for="{final_attrs["id"]}"'
            else:
                label_for = ''

            cb = forms.CheckboxInput(final_attrs, check_test=lambda v: v in str_values)
            option_value = str(tax[self.value])
            rendered_cb = cb.render(name, option_value, attrs=final_attrs)
            option_label = conditional_escape(str(tax[self.label]))

            if tax[self.label] == 0:
                output.append('<li>')
            else:
                output.append(f'<li style="margin-left: {tax[self.level] * 16}px;">')

            output.append(
                f'<div class="checkbox">'
                f'<div class="form-cat form-checkbox form-normal form-text" style="{self.label_css_style}" {label_for}>'
                f'{rendered_cb} <span class="text-muted">{option_label}</span>'
                f'</div></div>'
            )
            i += 1

        return mark_safe('\n'.join(output))


class QuillWidget(forms.Textarea):
    template_name = None

    class Media:
        css = {
            'all': ('https://cdn.quilljs.com/1.3.6/quill.snow.css',)
        }
        js = (
            'https://cdn.quilljs.com/1.3.6/quill.js',
        )

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ""

        final_attrs = self.build_attrs(attrs, extra_attrs={'name': name})
        html = f'''
        <div id="editor-{name}" style="height: 300px;">{value}</div>
        <textarea id="id_{name}" name="{name}" hidden>{value}</textarea>
        <script>
          document.addEventListener("DOMContentLoaded", function() {{
            var toolbarOptions = [
              [{{ 'font': [] }}],
              [{{ 'size': ['small', false, 'large', 'huge'] }}],
              ['bold', 'italic', 'underline', 'strike'],
              [{{ 'color': [] }}, {{ 'background': [] }}],
              [{{ 'script': 'sub'}}, {{ 'script': 'super' }}],
              [{{ 'header': [1, 2, 3, 4, 5, 6, false] }}],
              ['blockquote', 'code-block'],
              [{{ 'list': 'ordered'}}, {{ 'list': 'bullet' }}, {{ 'list': 'check' }}],
              [{{ 'indent': '-1'}}, {{ 'indent': '+1' }}],
              [{{ 'direction': 'rtl' }}],
              [{{ 'align': [] }}],
              ['link', 'image', 'video'],
              ['clean']
            ];

            var quill = new Quill("#editor-{name}", {{
              theme: "snow",
              modules: {{
                toolbar: toolbarOptions
              }}
            }});

            var textarea = document.getElementById("id_{name}");
            quill.on("text-change", function() {{
              textarea.value = quill.root.innerHTML;
            }});
          }});
        </script>
        '''
        return mark_safe(html)
