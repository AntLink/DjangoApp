from django import forms
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from nifty.widgets import (
    NiftySplitDateTimeWidget,
    MCDatePickerWidget,
)
from .utils import get_url_choice
from .models import MyPermission


class MyUserAddForm(UserCreationForm):
    def save(self, commit=True):
        user = super(MyUserAddForm, self).save()
        from .data import load_admin_theme_setting_stores
        from nifty.models import Setting
        load_admin_theme_setting_stores(Setting, user.pk)
        return user


class MyGroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'

    class Media:
        css = {
            'all': ('niftyv2/css/forms-multiselect.css',)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.fields['permissions'].queryset = MyPermission.objects.all()
        except KeyError:
            pass




class MyUserChangeForm(UserChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['redirect_url'] = self.instance.profile.redirect_url
        self.initial['gender'] = self.instance.profile.gender
        self.initial['address'] = self.instance.profile.address
        self.initial['phone_number'] = self.instance.profile.phone_number
        self.initial['place_of_birth'] = self.instance.profile.place_of_birth
        self.initial['birth_date'] = self.instance.profile.birth_date
        self.initial['facebook'] = self.instance.profile.facebook
        self.initial['twitter'] = self.instance.profile.twitter
        self.initial['google_plus'] = self.instance.profile.google_plus
        self.initial['instagram'] = self.instance.profile.instagram

        try:
            self.fields['user_permissions'].queryset = MyPermission.objects.all()
        except KeyError:
            pass

        self.initial['photo'] = self.instance.profile.get_profile_photo()

    class Media:
        css = {
            'all': ('niftyv2/css/forms-multiselect.css',)
        }
        js = [

        ]


    class Meta:
        model = User
        fields = '__all__'

        widgets = {
            'last_login': NiftySplitDateTimeWidget(attrs={'autocomplete': "off"}),
            'date_joined': NiftySplitDateTimeWidget(attrs={'autocomplete': "off"}),
        }

    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this "
            "user's password, but you can change the password using this form. "
        ),
    )

    photo = forms.CharField(
        widget=forms.TextInput,
        label=_('Photo profile'),
        help_text=_('Double click to change your profile photo'),
        required=False,
    )

    redirect_url = forms.CharField(
        widget=forms.Select(
            choices=get_url_choice(),
            attrs={'class': 'form-select', 'style': 'width:30%'}
        ),
        label=_('Default redirect URL'),
        help_text=_('For the default redirect after logging in, make sure it matches the User Staff Permissions you have chosen'),
        required=True,
    )

    gender = forms.CharField(
        widget=forms.Select(
            choices=(('male', _('Male')), ('female', _('Female')))
        ),
        label=_('Gender'),
        required=True,
    )

    address = forms.CharField(
        widget=forms.Textarea(),
        label=_('Address'),
        required=False,
    )

    phone_number = forms.CharField(
        widget=forms.TextInput(),
        label=_('Phone number'),
        required=False,
    )

    place_of_birth = forms.CharField(
        widget=forms.TextInput(),
        label=_('Place of birth'),
        required=True,
    )

    birth_date = forms.CharField(
        widget=MCDatePickerWidget(attrs={'autocomplete': "off"}),
        label=_('Birth date'),
        required=True,
    )

    facebook = forms.CharField(
        widget=forms.TextInput,
        label=_('Facebook link'),
        required=False,
    )

    twitter = forms.CharField(
        widget=forms.TextInput,
        label=_('Twitter link'),
        required=False,
    )

    google_plus = forms.CharField(
        widget=forms.TextInput,
        label=_('Google plus link'),
        required=False,
    )

    instagram = forms.CharField(
        widget=forms.TextInput,
        label=_('Instagram link'),
        required=False,
    )

    def save(self, commit=True):
        user = super(MyUserChangeForm, self).save(commit=False)
        if self.instance.pk:
            self.instance.profile.gender = self.cleaned_data.get('gender')
            self.instance.profile.address = self.cleaned_data.get('address')
            self.instance.profile.phone_number = self.cleaned_data.get('phone_number')
            self.instance.profile.place_of_birth = self.cleaned_data.get('place_of_birth')
            self.instance.profile.birth_date = self.cleaned_data.get('birth_date')
            self.instance.profile.redirect_url = self.cleaned_data.get('redirect_url')
            self.instance.profile.facebook = self.cleaned_data.get('facebook')
            self.instance.profile.twitter = self.cleaned_data.get('twitter')
            self.instance.profile.google_plus = self.cleaned_data.get('google_plus')
            self.instance.profile.instagram = self.cleaned_data.get('instagram')

            fo = self.cleaned_data.get('photo')
            photo = fo.split("/")
            self.instance.profile.photo = photo[(len(photo) - 1)]
            self.instance.profile.save()
        return user
