import json
from django import forms
from django.forms.widgets import Widget
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

class CKEditorWidget(Widget):
    template_name = 'admin/widgets/ckeditor_widget.html'

    class Media:
        css = {
            'all': (
                'niftyv2/vendors/ckeditor5/ckeditor5.css',
                'niftyv2/vendors/ckeditor5/premium-features.css',
                'niftyv2/vendors/ckeditor5/custom.css',
                'niftyv2/vendors/ckeditor5/dark.css',
                'niftyv2/vendors/ckeditor5/box-dark.css',
            )
        }
        js = (
            'niftyv2/vendors/ckeditor5/ckeditor5-custom.js',
            'niftyv2/vendors/ckeditor5/premium-features.js',
            'niftyv2/vendors/ckeditor5/ckbox-2.js',
        )

    def __init__(self, attrs=None, config=None):
        # Konfigurasi default
        default_config = {
            'baseUrl': 'http://127.0.0.1:8090',
            'emoji_lang_url':'http://127.0.0.1:8090/static/niftyv2/vendors/ckeditor5/emoji-en.json',
            'ai_api_key': 'c043b4797fd245cf9d104dddda39a383.P8hW0m9To6Lf1rIC',
            # 'ai_api_url': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            'ai_api_url': 'https://api.z.ai/api/paas/v4/chat/completions',
            'ai_model': "glm-4.5-flash",
            'ai_temperature': 0.8,
            'ai_top_p': 1,
            'cloud_services_api_url': 'http://127.0.0.1:8090/api/',
            'placeholder': 'Type or paste your content here!',
            'license_key': '-',
            'tokenUrl': '/api/auth/login',
            'refreshTokenUrl': '/api/auth/token-refresh',
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