from django.forms import TextInput, Select, Textarea
from django.utils.safestring import mark_safe
from django import forms
from django.urls import reverse_lazy
import json
from django.templatetags.static import static
from . import utils

django_version = utils.django_major_version()


class NumberInput(TextInput):
    """
    HTML5 Number input
    Left for backwards compatibility
    """
    input_type = 'number'


class HTML5Input(TextInput):
    """
    Supports any HTML5 input
    http://www.w3schools.com/html/html5_form_input_types.asp
    """

    def __init__(self, attrs=None, input_type=None):
        self.input_type = input_type
        super(HTML5Input, self).__init__(attrs)


#
class LinkedSelect(Select):
    """
    Linked select - Adds link to foreign item, when used with foreign key field
    """

    def __init__(self, attrs=None, choices=()):
        attrs = _make_attrs(attrs, classes="linked-select")
        super(LinkedSelect, self).__init__(attrs, choices)


class EnclosedInput(TextInput):
    """
    Widget for bootstrap appended/prepended inputs
    """

    def __init__(self, attrs=None, prepend=None, append=None):
        """
        For prepend, append parameters use string like %, $ or html
        """
        self.prepend = prepend
        self.append = append
        super(EnclosedInput, self).__init__(attrs=attrs)

    def enclose_value(self, value):
        """
        If value doesn't starts with html open sign "<", enclose in add-on tag
        """
        if value.startswith("<"):
            return value
        if value.startswith("icon-"):
            value = '<i class="%s"></i>' % value
        return '<span class="add-on">%s</span>' % value

    def render(self, name, value, attrs=None, renderer=None):
        if django_version < (2, 0):
            output = super(EnclosedInput, self).render(name, value, attrs)
        else:
            output = super(EnclosedInput, self).render(name, value, attrs, renderer)

        div_classes = []
        if self.prepend:
            div_classes.append('input-prepend')
            self.prepend = self.enclose_value(self.prepend)
            output = ''.join((self.prepend, output))
        if self.append:
            div_classes.append('input-append')
            self.append = self.enclose_value(self.append)
            output = ''.join((output, self.append))

        return mark_safe(
            '<div class="%s">%s</div>' % (' '.join(div_classes), output))


class AutosizedTextarea(Textarea):
    """
    Autosized Textarea - textarea height dynamically grows based on user input
    """

    def __init__(self, attrs=None):
        new_attrs = _make_attrs(attrs, {"rows": 2}, "autosize")
        super(AutosizedTextarea, self).__init__(new_attrs)

    @property
    def media(self):
        return forms.Media(js=[static("nifty/js/jquery.autosize-min.js")])

    def render(self, name, value, attrs=None, renderer=None):
        if django_version < (2, 0):
            output = super(AutosizedTextarea, self).render(name, value, attrs)
        else:
            output = super(AutosizedTextarea, self).render(name, value, attrs, renderer)

        output += mark_safe(
            "<script type=\"text/javascript\">Suit.$('#id_%s').autosize();</script>"
            % name)
        return output


class MCDatePickerWidget(forms.TextInput):
    class Media:
        css = {
            'all': (
                "niftyv2/pages/date-time-picker.min.css",
            )
        }
        js = (
            "niftyv2/pages/date-time-picker.min.js",
        )

    def __init__(self, attrs=None, format=None, input_width="30%"):
        self.input_width = input_width  # simpan custom width
        default_attrs = {'class': 'form-control', 'autocomplete': 'off'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        element_id = attrs.get("id") if attrs else f"id_{name}"
        button_id = f"btn_{element_id}"

        html = f"""
        <div class="input-group mb-3" style="width:{self.input_width}">
            {input_html}
            <button type="button" class="btn btn-primary" id="{button_id}">
                <i class="demo-pli-calendar-4 fs-5"></i>
            </button>
        </div>

        <script>
        document.addEventListener("DOMContentLoaded", function () {{
            if (!window.mcPicker_{element_id}) {{
                const picker = MCDatepicker.create({{
                    el: "#{element_id}",
                    dateFormat: "YYYY-MM-DD",
                    bodyType: "modal",
                    autoClose: true
                }});
                window.mcPicker_{element_id} = picker;

                document.getElementById("{button_id}").addEventListener("click", function() {{
                    picker.open();
                }});
            }}
        }});
        </script>
        """
        return mark_safe(html)


class NiftyTimeWidget(forms.TextInput):
    width = '20%'

    def __init__(self, attrs=None, width='25%'):
        self.width = width
        defaults = {'placeholder': '00:00:00'}
        new_attrs = _make_attrs(attrs, defaults, "form-control time-form")
        super(NiftyTimeWidget, self).__init__(attrs=new_attrs)

    @property
    def media(self):
        js = [
            'nifty/plugins/bootstrap-timepicker/bootstrap-timepicker.min.js',
            'nifty/js/niftytime.js',
        ]
        css = {
            "all": (
                "nifty/plugins/bootstrap-timepicker/bootstrap-timepicker.min.css",
            )
        }
        return forms.Media(js=["%s" % path for path in js], css=css)

    def render(self, name, value, attrs=None, renderer=None):
        if django_version < (2, 0):
            output = super(NiftyTimeWidget, self).render(name, value, attrs)
        else:
            output = super(NiftyTimeWidget, self).render(name, value, attrs, renderer)
        return mark_safe('<div class="input-group date" style="width:%s">%s<span class="input-group-addon"><i class="demo-pli-clock"></i></span></div>' % output)


class NiftySplitDateTimeWidget(forms.SplitDateTimeWidget):
    """
    A SplitDateTime Widget that has some admin-specific styling.
    """

    template_name = 'nifty/widgets/datetime.html'

    def __init__(self, attrs=None):
        widgets = [MCDatePickerWidget, NiftyTimeWidget]
        forms.MultiWidget.__init__(self, widgets, attrs)

    if django_version < (1, 11):
        def format_output(self, rendered_widgets):
            out_tpl = '<div id="demo-dp-component" style="display:inline-flex;">%s %s</div>'
            return mark_safe(out_tpl % (rendered_widgets[0], rendered_widgets[1]))
    else:
        def render(self, name, value, attrs=None, renderer=None):
            output = super(NiftySplitDateTimeWidget, self).render(name, value, attrs, renderer)
            return mark_safe('<div id="demo-dp-component" style="display:inline-flex;">%s</div>' % output)


class NiftyMultipleSelect(forms.SelectMultiple):
    class Media:
        css = {
            'all': ('nifty/css/forms-select.css',)
        }


def _make_attrs(attrs, defaults=None, classes=None):
    result = defaults.copy() if defaults else {}
    if attrs:
        result.update(attrs)
    if classes:
        result["class"] = " ".join((classes, result.get("class", "")))
    return result


class CKEditorWidget(forms.Widget):
    template_name = None

    class Media:
        css = {
            'all': (
                'niftyv2/vendors/ckeditor5/style.css',
                'niftyv2/vendors/ckeditor5/ckeditor5.css',
                'niftyv2/vendors/ckeditor5/premium-features.css',
                'niftyv2/vendors/ckeditor5/dark.css',
                'niftyv2/vendors/ckeditor5/box-dark.css',
            )
        }
        js = (
            'niftyv2/vendors/ckeditor5/ckeditor5ai.js',
            'niftyv2/vendors/ckeditor5/premium-features.js',
            # 'niftyv2/vendors/ckeditor5/ckboxcustom.js',
            'niftyv2/vendors/ckeditor5/ckbox-style.js',
            'niftyv2/vendors/ckeditor5/ckbox-qs.js',
            'niftyv2/vendors/ckeditor5/ckbox-wc.js',
            'niftyv2/vendors/ckeditor5/ckbox-2.8.2-custom.js',
        )

    def __init__(self, attrs=None, config=None):
        # Konfigurasi default
        default_config = {
            'ai_api_key': '09ac094bc293454b94457cf556ee8616.opW0YYeFQce1AA0m',
            'ai_api_url': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            'ai_model': "glm-4.5-flash",
            'ai_temperature': 0.8,
            'ai_top_p': 1,
            'cloud_services_token_url': 'http://127.0.0.1:8090/static/niftyv2/vendors/ckeditor5/token',

            'jwt_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU4OTcxODMzLCJpYXQiOjE3NTg5NTAyMzMsImp0aSI6ImQ5ZDlhYjYxYjljNTQxMDFhNDk0MmExNmM2Mjg1ZWE4IiwidXNlcl9pZCI6IjEiLCJhdWQiOiJ6QkdwbENKOGs5RHM1U0wwY3lubyIsInN1YiI6IjEiLCJhdXRoIjp7ImNrYm94Ijp7InJvbGUiOiJhZG1pbiIsIndvcmtzcGFjZXMiOlsxMl19fX0.Q49EoVQ0vINdoTg1fKc61DBGwZKUPqcT5vk4LdDTbOU',
            # 'cloud_services_token_url': 'http://127.0.0.1:8090/api/auth/token',
            'cloud_services_api_url': 'http://127.0.0.1:8090/api/',
            'placeholder': 'Type or paste your content here!',
            'license_key': '-',
            'initial_data': '',
        }

        # Gabungkan dengan konfigurasi kustom jika ada
        if config:
            default_config.update(config)

        self.config = default_config
        default_attrs = {'id': 'editor'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ""

        js_config = json.dumps(self.config)

        html = f"""
        <textarea id="editor-{name}" name="{name}" hidden>{value}</textarea>
        <script>
        

        document.addEventListener('DOMContentLoaded', function() {{
            const {{
                ClassicEditor,Alignment,Autoformat,AutoImage,AutoLink,Autosave,BalloonToolbar,BlockQuote,BlockToolbar,Bold,
                Bookmark,CKBox,CKBoxImageEdit,CloudServices,Code,CodeBlock,Emoji,Essentials,FindAndReplace,FontBackgroundColor,FontColor,FontFamily,
                FontSize,Fullscreen,GeneralHtmlSupport,Heading,Highlight,HorizontalLine,ImageBlock,ImageCaption,ImageEditing,ImageInline,
                ImageInsert,ImageInsertViaUrl,ImageResize,ImageStyle,ImageTextAlternative,ImageToolbar,ImageUpload,ImageUtils,Indent,
                IndentBlock,Italic,Link,LinkImage,List,ListProperties,MediaEmbed,Mention,PageBreak,Paragraph,PasteFromMarkdownExperimental,PasteFromOffice,
                PictureEditing,PlainTableOutput,RemoveFormat,ShowBlocks,SourceEditing,SpecialCharacters,SpecialCharactersArrows,SpecialCharactersCurrency,
                SpecialCharactersEssentials,SpecialCharactersLatin,SpecialCharactersMathematical,SpecialCharactersText,Strikethrough,Subscript,Superscript,Table,
                TableCaption,TableCellProperties,TableColumnResize,TableLayout,TableProperties,TableToolbar,TextTransformation,TodoList, Underline
            }} = window.CKEDITOR;
            const {{ AIAssistant, OpenAITextAdapter,SourceEditingEnhanced,ExportPdf, ExportWord, ImportWord,PasteFromOfficeEnhanced }} = window.CKEDITOR_PREMIUM_FEATURES;
            const config = {js_config};
            const editorConfig = {{
                ui: {{ viewportOffset: {{ top: 53 }} }},
                toolbar: {{
                    items: [
                        'fullscreen','|','undo','redo','|','importWord','exportWord','exportPdf','SourceEditingEnhanced','|','aiCommands','aiAssistant','|','heading',
                        'sourceEditing','showBlocks','findAndReplace','|','insertImage','CKBox','mediaEmbed','|',
                        'insertTable','insertTableLayout','|','alignment','bulletedList','numberedList',
                        'todoList','outdent','indent','|','fontSize','fontFamily','fontColor','fontBackgroundColor',
                        '|','bold','italic','underline','strikethrough','subscript','superscript','code',
                        'removeFormat','|','emoji','specialCharacters','horizontalLine','pageBreak','link',
                        'bookmark','highlight','blockQuote','codeBlock'
                    ],
                    shouldNotGroupWhenFull: false
                }},
                plugins: [
                    AIAssistant,OpenAITextAdapter,SourceEditingEnhanced, Alignment, Autoformat, AutoImage, AutoLink, Autosave, BalloonToolbar, BlockQuote,
                    BlockToolbar, Bold, Bookmark, CKBox, CKBoxImageEdit, CloudServices, Code, CodeBlock, Emoji,
                    Essentials, FindAndReplace, FontBackgroundColor, FontColor, FontFamily, FontSize, Fullscreen,
                    GeneralHtmlSupport, Heading, Highlight, HorizontalLine, ImageBlock, ImageCaption, ImageEditing,
                    ImageInline, ImageInsert, ImageInsertViaUrl, ImageResize, ImageStyle, ImageTextAlternative,
                    ImageToolbar, ImageUpload, ImageUtils, Indent, IndentBlock, Italic, Link, LinkImage, List,
                    ListProperties, MediaEmbed, Mention, PageBreak, Paragraph,ExportPdf,ExportWord,ImportWord,
                    PasteFromMarkdownExperimental, PasteFromOffice, PictureEditing, PlainTableOutput, RemoveFormat,
                    ShowBlocks, SourceEditing, SpecialCharacters, SpecialCharactersArrows, SpecialCharactersCurrency,
                    SpecialCharactersEssentials, SpecialCharactersLatin, SpecialCharactersMathematical,
                    SpecialCharactersText, Strikethrough, Subscript, Superscript, Table, TableCaption,
                    TableCellProperties, TableColumnResize, TableLayout, TableProperties, TableToolbar,
                    TextTransformation, TodoList, Underline,
                ],
                balloonToolbar: ['aiAssistant', '|', 'bold', 'italic', '|', 'link', 'insertImage', '|', 'bulletedList', 'numberedList','emoji','specialCharacters','horizontalLine','pageBreak','link'],
                blockToolbar: ['fontSize','fontColor','fontBackgroundColor','|','bold','italic','|','link','insertImage','insertTable','insertTableLayout','|','bulletedList','numberedList','outdent','indent'],
                ckbox: {{
                    theme: document.documentElement.getAttribute("data-bs-theme")
                }},
                licenseKey: config.license_key,
                cloudServices: {{
                    // tokenUrl: config.cloud_services_token_url,
                    tokenUrl: config.jwt_token,
                    ApiURL: config.cloud_services_api_url
                }},
                image: {{
                    toolbar: ['toggleImageCaption','imageTextAlternative','|','imageStyle:inline','imageStyle:wrapText','imageStyle:breakText','|','resizeImage','|','ckboxImageEdit']
                }},
                ai: {{
                    openAI: {{
                        apiUrl: config.ai_api_url,
                        requestParameters: {{
                            model: config.ai_model,
                            stream: true,
                            temperature: config.temperature,
                            top_p: 1
                        }},
                        requestHeaders: {{
                            Authorization: 'Bearer ' + config.ai_api_key
                        }}
                    }}
                }},
                placeholder: config.placeholder
            }};
            ClassicEditor.create(document.querySelector('#editor-{name}'), editorConfig);
        }});
        </script>
        """
        return mark_safe(html)
