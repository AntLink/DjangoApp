import json
from django import forms
from .models import Image, Tags
from .widgets import FileMediaSingleImage, FileMediaSingleFile
from .search import BaseSearchForm
# from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext_lazy as _


class UploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['file']


class FileForm(BaseSearchForm):
    class Media:
        css = {
            'all': ('nifty/css/forms-select.css',)
        }

    files = forms.CharField(
        widget=FileMediaSingleFile,
        label=_('File'),
        help_text=_('Double click to change your file.'),
        required=True,
    )

    description = forms.CharField(
        label=_('Description'),
        widget=forms.Textarea,
        required=False,
        max_length=255,
        help_text=_('Maximum can be entered is 255 text characters')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data = [{
            'id': self.instance.pk,
            'value': self.instance.file.name,
        }]
        self.initial['files'] = json.dumps(data)
        try:
            self.fields['relationships'].queryset = Tags.objects.filter(type='f')
        except KeyError:
            pass


class ImageForm(BaseSearchForm):
    class Media:
        css = {
            'all': ('nifty/css/forms-select.css',)
        }

    description = forms.CharField(
        label=_('Description'),
        widget=forms.Textarea,
        required=False,
        max_length=255,
        help_text=_('Maximum can be entered is 255 text characters')
    )

    image = forms.CharField(
        widget=FileMediaSingleImage(),
        label=_('Image'),
        help_text=_('Double click to change your image.'),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        data = [{
            'id': self.instance.pk,
            'value': self.instance.get_image('150x150'),
        }]
        self.initial['image'] = json.dumps(data)
        try:
            self.fields['relationships'].queryset = Tags.objects.filter(type='p')
        except KeyError:
            pass

    class Meta:
        model = Image
        fields = ['file', 'name', 'description']
        base_qs = Image.objects
        search_fields = ('name', 'description')
        fulltext_indexes = (
            ('name', 2),  # name matches are weighted higher
            ('name, description, id', 1),
        )


class TagsForm(forms.ModelForm):
    class Meta:
        model = Tags
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # qs = Tags.objects.filter().all()
        # qs = qs.exclude(pk=self.instance.pk)
        # self.fields['parent'].queryset = qs
