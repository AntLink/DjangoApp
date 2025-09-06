from django import forms
from django.utils.translation import gettext_lazy as _
from .widgets import MCDatePickerWidget
from filemedia.widgets import FileMediaPhoto

class UserProfileForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.user.first_name
        self.fields['last_name'].initial = self.user.last_name
        self.fields['gender'].initial = self.user.profile.gender
        self.fields['email'].initial = self.user.email
        self.fields['phone_number'].initial = self.user.profile.phone_number
        self.fields['address'].initial = self.user.profile.address
        self.fields['place_of_birth'].initial = self.user.profile.place_of_birth
        self.fields['birth_date'].initial = self.user.profile.birth_date
        self.fields['facebook'].initial = self.user.profile.facebook
        self.fields['twitter'].initial = self.user.profile.twitter
        self.fields['google_plus'].initial = self.user.profile.google_plus
        self.fields['instagram'].initial = self.user.profile.instagram

        # from django.core.exceptions import ObjectDoesNotExist
        # try:
        #     if self.instance.is_superuser:
        #         media = Media.objects.get(unique_name=self.instance.profile.photo).pk
        #     else:
        #         media = self.instance.media_set.get(unique_name=self.instance.profile.photo).pk
        # except ObjectDoesNotExist:
        #     media = None
        #
        # data = [{
        #     'id': media,
        #     'value': self.instance.profile.get_profile_photo(),
        # }]
        # self.initial['photo'] = json.dumps(data)
        self.initial['photo'] = self.user.profile.get_profile_photo()

    photo = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'readonly': 'readonly'}
        ),
        label=_('Photo profile'),
        help_text=_('Double click to change your profile photo'),
        required=False,
    )

    first_name = forms.CharField(
        label=_('First name'),
        required=True,
    )
    last_name = forms.CharField(
        label=_('Last name'),
        required=True,
    )
    gender = forms.CharField(
        widget=forms.Select(
            choices=(('male', _('Male')), ('female', _('Female'))),
            attrs={'class': 'selectpicker'}
        ),
        label=_('Gender'),
        required=True,
    )
    email = forms.CharField(
        widget=forms.EmailInput,
        label=_('Email'),
        required=True,
    )
    phone_number = forms.CharField(
        label=_('Phone number'),
        required=True,
    )
    address = forms.CharField(
        widget=forms.Textarea,
        label=_('Address'),
        required=True,
    )
    place_of_birth = forms.CharField(

        label=_('Place of birth'),
        required=True,
    )
    birth_date = forms.CharField(
        widget=MCDatePickerWidget(attrs={'autocomplete': "off"}),
        label=_('Birth date'),
        required=True,
    )
    facebook = forms.CharField(
        label=_('Facebook link'),
        required=False,
    )
    twitter = forms.CharField(
        label=_('Twitter link'),
        required=False,
    )
    google_plus = forms.CharField(
        label=_('Google plus link'),
        required=False,
    )
    instagram = forms.CharField(
        label=_('Instagram link'),
        required=False,
    )

class ActionForm(forms.Form):
    class Media:
        js = [
            'niftyv2/js/suitcheckbox.js',
            # 'niftyv2/js/form-validations.js'
        ]

    action = forms.ChoiceField(label=_('Action:'), required=False, initial=0)
    select_across = forms.BooleanField(
        label='',
        required=False,
        initial=0,
        widget=forms.HiddenInput({'class': 'select-across'}),
    )


class AdminSettingForm(forms.Form):

    def __init__(self, user, setting, *args, **kwargs):
        self.setting = setting
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['admin_site_title'].initial = self.setting.objects.get(value='admin_site_title').content
        self.fields['admin_brand_title'].initial = self.setting.objects.get(value='admin_brand_title').content
        self.fields['admin_site_favicon'].initial = self.setting.objects.get(value='admin_site_favicon').content
        self.fields['admin_site_logo'].initial = self.setting.objects.get(value='admin_site_logo').content
        self.fields['admin_email_address'].initial = self.setting.objects.get(value='admin_email_address').content
        self.fields['admin_site_copyright'].initial = self.setting.objects.get(value='admin_site_copyright').content
        self.fields['admin_phone'].initial = self.setting.objects.get(value='admin_phone').content
        self.fields['admin_address'].initial = self.setting.objects.get(value='admin_address').content

    admin_site_title = forms.CharField(
        label=_('Title'),
        required=True,
    )

    admin_brand_title = forms.CharField(
        label=_('Brand Title'),
        required=True,
    )

    admin_site_favicon = forms.CharField(
        label=_('Favicon'),
        required=True,
    )

    admin_site_logo = forms.CharField(
        label=_('Logo'),
        required=True,
    )

    admin_site_copyright = forms.CharField(
        label=_('Copyright'),
        required=True,
    )

    admin_email_address = forms.CharField(
        widget=forms.EmailInput(),
        label=_('Email address'),
        required=True,
    )

    admin_phone = forms.CharField(
        label=_('Phone'),
        required=True,
    )

    admin_address = forms.CharField(
        widget=forms.Textarea(),
        label=_('Address'),
        required=True,
    )

    def log_change(self, user, object, message):
        from django.contrib.admin.models import LogEntry, CHANGE
        from django.contrib.admin.options import get_content_type_for_model
        return LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=CHANGE,
            change_message=message,
        )

    def save(self, commit=True):
        for v in self.changed_data:
            st = self.setting.objects.get(value=v, type='admin')
            st.content = self.cleaned_data.get(v)
            if commit:
                change_message = [{
                    'action': 'Updated',
                    'fields': {
                        v: self.cleaned_data.get(v)
                    }
                }]
                st.save()
                self.log_change(self.user, st, change_message)


class SiteSettingForm(forms.Form):
    def __init__(self, user, setting, *args, **kwargs):
        self.setting = setting
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['site_title'].initial = self.setting.objects.get(value='site_title').content
        self.fields['site_tag'].initial = self.setting.objects.get(value='site_tag').content
        self.fields['site_language'].initial = self.setting.objects.get(value='site_language').content
        self.fields['site_email_address'].initial = self.setting.objects.get(value='site_email_address').content
        self.fields['site_timezon'].initial = self.setting.objects.get(value='site_timezon').content
        self.fields['site_date_format'].initial = self.setting.objects.get(value='site_date_format').content
        self.fields['site_keyword'].initial = self.setting.objects.get(value='site_keyword').content
        self.fields['site_author'].initial = self.setting.objects.get(value='site_author').content
        self.fields['site_description'].initial = self.setting.objects.get(value='site_description').content
        self.fields['facebook_page'].initial = self.setting.objects.get(value='facebook_page').content
        self.fields['twitter_page'].initial = self.setting.objects.get(value='twitter_page').content
        self.fields['google_plus_page'].initial = self.setting.objects.get(value='google_plus_page').content
        self.fields['instagram_page'].initial = self.setting.objects.get(value='instagram_page').content

    site_title = forms.CharField(
        label=_('Title'),
        required=True,
    )

    site_tag = forms.CharField(
        label=_('Tag'),
        required=True
    )

    site_language = forms.CharField(
        label=_('Language'),
        required=True
    )

    site_email_address = forms.CharField(
        label=_('Email Address'),
        required=True
    )

    site_timezon = forms.CharField(
        label=_('Timezon'),
        required=True
    )

    site_date_format = forms.CharField(
        label=_('Date Format'),
        required=True
    )

    site_keyword = forms.CharField(
        label=_('Keyword'),
        required=True
    )

    site_author = forms.CharField(
        label=_('Author'),
        required=True
    )

    site_description = forms.CharField(
        widget=forms.Textarea,
        label=_('Description'),
        required=True
    )

    facebook_page = forms.CharField(
        label=_('Facebook link'),
        required=True
    )

    twitter_page = forms.CharField(
        label=_('Twitter link'),
        required=True
    )

    google_plus_page = forms.CharField(
        label=_('Googlr plus link'),
        required=True
    )

    instagram_page = forms.CharField(
        label=_('Instagram'),
        required=True
    )


    def log_change(self, user, object, message):
        from django.contrib.admin.models import LogEntry, CHANGE
        from django.contrib.admin.options import get_content_type_for_model
        return LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=CHANGE,
            change_message=message,
        )

    def save(self, commit=True):
        for v in self.changed_data:
            st = self.setting.objects.get(value=v, type='site')
            st.content = self.cleaned_data.get(v)
            if commit:
                change_message = [{
                    'action': 'Updated',
                    'fields': {
                        v: self.cleaned_data.get(v)
                    }
                }]
                st.save()
                self.log_change(self.user, st, change_message)
