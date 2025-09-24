# accounts/widgets.py
from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.conf import settings

class ProfileImageWidget(forms.ClearableFileInput):
    template_name = 'admin/widgets/profile_image_widget.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'accept': 'image/*',
            'class': 'profile-input',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)

        # Handle URL image dengan lebih robust
        current_image_url = ""
        is_initial = False

        # Debug: print type dan value untuk troubleshooting
        print(f"DEBUG - Value type: {type(value)}, Value: {value}")

        if value:
            # Case 1: Value adalah instance model FieldFile (mempunyai atribut url)
            if hasattr(value, 'url'):
                current_image_url = value.url
                is_initial = True
                print(f"DEBUG - Using value.url: {current_image_url}")

            # Case 2: Value adalah string path relatif
            elif isinstance(value, str) and value:
                # Pastikan tidak ada double slash dalam URL
                media_url = settings.MEDIA_URL
                if media_url.endswith('/') and value.startswith('/'):
                    value = value[1:]
                current_image_url = f"{media_url}{value}"
                is_initial = True
                print(f"DEBUG - Constructed URL: {current_image_url}")

            # Case 3: Value adalah dict atau object lain yang berisi path
            elif hasattr(value, 'name'):
                # Untuk case dimana value adalah file object tetapi bukan FieldFile
                current_image_url = f"{settings.MEDIA_URL}{value.name}"
                is_initial = True
                print(f"DEBUG - Using value.name: {current_image_url}")

        extra_context = {
            'widget_name': name,
            'widget_id': attrs.get('id', f'id_{name}'),
            'current_image_url': current_image_url,
            'is_initial': is_initial,
        }
        context.update(extra_context)

        return mark_safe(render_to_string(self.template_name, context))

    class Media:
        css = {
            'all': ('users/css/profile_upload.css',)
        }
        js = ('users/js/profile_upload.js',)
