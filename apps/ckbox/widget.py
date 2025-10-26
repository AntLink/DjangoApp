import json
from django import forms
from django.forms.widgets import Widget
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.conf import settings

class CKEditorWidget(Widget):
    template_name = 'ckbox/widgets/ckeditor_widget.html'

    class Media:
        css = {
            'all': (
                'ckbox/css/ckeditor5.css',
                'ckbox/css/premium-features.css',
                'ckbox/css/custom.css',
                'ckbox/css/dark.css',
                'ckbox/css/box-dark.css',
            )
        }
        js = (
            'ckbox/js/ckeditor5-custom.js',
            'ckbox/js/premium-features.js',
            'ckbox/js/ckbox-2.js',
        )

    def __init__(self, attrs=None, config=None):
        # Konfigurasi default
        default_config = {
            'baseUrl': settings.CKEDITOR_BASE_URL,
            'emoji_lang_url':settings.CKEDITOR_EMOJI_LANG,
            'ai_api_key': settings.CKEDITOR_AI_API_KEY,
            'ai_api_url': settings.CKEDITOR_AI_API_URL,
            'ai_model': settings.CKEDITOR_AI_MODEL,
            'ai_temperature': settings.CKEDITOR_AI_TEMPERATURE,
            'ai_top_p': settings.CKEDITOR_AI_TOP_P,
            'cloud_services_api_url': settings.CKEDITOR_API_URL,
            'placeholder': settings.CKEDITOR_PLACEHOLDER,
            'license_key': settings.CKEDITOR_LICENSE_KEY,
            'tokenUrl': settings.CKEDITOR_TOKEN_URL,
            'refreshTokenUrl': settings.CKEDITOR_REFRESH_TOKEN_URL,
            'plugins': settings.CKEDITOR_PLUGIN,
        }

        # Gabungkan dengan konfigurasi kustom jika ada
        if config:
            default_config.update(config)

        self.config = default_config
        default_attrs = {'id': 'ckeditor'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ""

        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['name'] = name

        if 'id' not in final_attrs:
            final_attrs['id'] = f'id_{name}'

        context = {
            'widget': {
                'attrs': final_attrs,
                'value': value,
                'config_json': json.dumps(self.config),
                'name': name,
            }
        }

        return mark_safe(render_to_string(self.template_name, context))