from django.utils.translation import gettext_lazy as _

from .models import Setting
# from ..data import load_general_setting_stores, load_theme_setting_stores, load_themes_stores

def load_admin_setting_stores(user_id=None):
    #Setting = apps.get_model("nifty", "Setting")

    admin_site_title = Setting(
        user_id=user_id,
        name=_('Title'),
        value='admin_site_title',
        content='AntLink administrator',
        type='admin',
        autoload='yes'
    )
    admin_site_title.save()

    admin_brand_title = Setting(
        user_id=user_id,
        name=_('Brand Title'),
        value='admin_brand_title',
        content='AntLink',
        type='admin',
        autoload='yes'
    )
    admin_brand_title.save()

    admin_site_favicon = Setting(
        user_id=user_id,
        name=_('Favicon'),
        value='admin_site_favicon',
        content='/static/nifty/img/favicon.png',
        type='admin',
        autoload='yes'
    )

    admin_site_favicon.save()

    admin_site_logo = Setting(
        user_id=user_id,
        name=_('Logo'),
        value='admin_site_logo',
        content='/static/nifty/img/logo.png',
        type='admin',
        autoload='yes'
    )

    admin_site_logo.save()

    admin_site_copyright = Setting(
        user_id=user_id,
        name=_('Copyright'),
        value='admin_site_copyright',
        content='AntLink',
        type='admin',
        autoload='yes'
    )

    admin_site_copyright.save()

    admin_email = Setting(
        user_id=user_id,
        name=_('Email'),
        value='admin_email_address',
        content='admin@example.com',
        type='admin',
        autoload='yes'
    )
    admin_email.save()

    admin_phone = Setting(
        user_id=user_id,
        name=_('Phone'),
        value='admin_phone',
        content='0818345070',
        type='admin',
        autoload='yes'
    )
    admin_phone.save()

    admin_address = Setting(
        user_id=user_id,
        name=_('Address'),
        value='admin_address',
        content='Jln. Suasembada 11 No.5 BTN Kehutanan Krg.Pule Sekarbela Mataram Nusa Tenggara Barat (NTB) Indonesia',
        type='admin',
        autoload='yes'
    )
    admin_address.save()



def load_site_setting_stores(user_id=None):
    #Setting = apps.get_model("nifty", "Setting")

    site_title = Setting(
        user_id=user_id,
        name=_('Title'),
        value='site_title',
        content='Site Title',
        type='site',
        autoload='yes'
    )
    site_title.save()

    tag_line = Setting(
        user_id=user_id,
        name=_('Tags'),
        value='site_tag',
        content='Site tag',
        type='site',
        autoload='yes'
    )
    tag_line.save()

    site_language = Setting(
        user_id=user_id,
        name=_('Language'),
        value='site_language',
        content='id',
        type='site',
        autoload='yes'
    )
    site_language.save()

    email = Setting(
        user_id=user_id,
        name=_('Email Address'),
        value='site_email_address',
        content='admin@example.com',
        type='site',
        autoload='yes'
    )
    email.save()

    timezone = Setting(
        user_id=user_id,
        name=_('Timezone'),
        value='site_timezon',
        content='Asia/Makasar',
        type='site',
        autoload='yes'
    )
    timezone.save()

    date_format = Setting(
        user_id=user_id,
        name=_('Date Format'),
        value='site_date_format',
        content='yyyy/dd/mm',
        type='site',
        autoload='yes'
    )
    date_format.save()

    site_keyword = Setting(
        user_id=user_id,
        name=_('Keyword'),
        value='site_keyword',
        content='Site Meta Keyword',
        type='site',
        autoload='yes'
    )
    site_keyword.save()

    site_author = Setting(
        user_id=user_id,
        name=_('Author'),
        value='site_author',
        content='Site Author',
        type='site',
        autoload='yes'
    )
    site_author.save()

    site_description = Setting(
        user_id=user_id,
        name=_('Description'),
        value='site_description',
        content='Site Description',
        type='site',
        autoload='yes'
    )
    site_description.save()

    facebook_page = Setting(
        user_id=user_id,
        name=_('Facebook'),
        value='facebook_page',
        content='http://www.facebook.com',
        type='site',
        autoload='yes'
    )
    facebook_page.save()

    twitter_page = Setting(
        user_id=user_id,
        name=_('Twitter'),
        value='twitter_page',
        content='http://www.twitter.com',
        type='site',
        autoload='yes'
    )
    twitter_page.save()

    google_plus_page = Setting(
        user_id=user_id,
        name=_('Google Pluse'),
        value='google_plus_page',
        content='http://plus.google.com',
        type='site',
        autoload='yes'
    )
    google_plus_page.save()

    instagram_page = Setting(
        user_id=user_id,
        name=_('Instagram'),
        value='instagram_page',
        content='http://www.instagram.com',
        type='site',
        autoload='yes'
    )
    instagram_page.save()


def load_admin_theme_setting_stores(user_id=None):
    #Setting = apps.get_model("nifty", "Setting")

    admin_colpase_menu = Setting(
        user_id=user_id,
        name=_('Navigation Collapsed Mode'),
        value='admin_colpase_menu',
        content='mainnav-lg',
        type='admin_theme',
        autoload='yes'
    )
    admin_colpase_menu.save()

    admin_navbar_fixed = Setting(
        user_id=user_id,
        name=_('Navbar Fixed Position'),
        value='admin_navbar_fixed',
        content='navbar-fixed',
        type='admin_theme',
        autoload='yes'
    )
    admin_navbar_fixed.save()

    admin_navbar_show_menu = Setting(
        user_id=user_id,
        name=_('Navbar Show Menu'),
        value='admin_navbar_show_menu',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_navbar_show_menu.save()

    admin_navbar_show_usermenu = Setting(
        user_id=user_id,
        name=_('Navbar Show User Menu'),
        value='admin_navbar_show_usermenu',
        content='nav-user-menu',
        type='admin_theme',
        autoload='yes'
    )
    admin_navbar_show_usermenu.save()

    admin_mainnav_show_menu = Setting(
        user_id=user_id,
        name=_('Navigation Show Menu'),
        value='admin_nav_show_menu',
        content='nav-show-menu',
        type='admin_theme',
        autoload='yes'
    )
    admin_mainnav_show_menu.save()

    admin_mainnav_fixed = Setting(
        user_id=user_id,
        name=_('Navigation Fixed Position'),
        value='admin_mainnav_fixed',
        content='mainnav-fixed',
        type='admin_theme',
        autoload='yes'
    )
    admin_mainnav_fixed.save()

    admin_footer_fixed = Setting(
        user_id=user_id,
        name=_('Footer Fixed Position'),
        value='admin_footer_fixed',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_footer_fixed.save()

    admin_mainnav_offcanvas = Setting(
        user_id=user_id,
        name=_('Navigation Off Canvas'),
        value='admin_mainnav_offcanvas',
        content='none',
        type='admin_theme',
        autoload='yes'
    )
    admin_mainnav_offcanvas.save()

    admin_mainnav_profile = Setting(
        user_id=user_id,
        name=_('Navigation Widget Profil'),
        value='admin_mainnav_profile',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_mainnav_profile.save()

    admin_mainnav_shortcut = Setting(
        user_id=user_id,
        name=_('Navigation Shortcut Buttons'),
        value='admin_mainnav_shortcut',
        content='hidden',
        type='admin_theme',
        autoload='yes'
    )
    admin_mainnav_shortcut.save()

    admin_theme_animation = Setting(
        user_id=user_id,
        name=_('Theme Animations'),
        value='admin_theme_animation',
        content='effect',
        type='admin_theme',
        autoload='yes'
    )
    admin_theme_animation.save()

    admin_enable_theme_animation = Setting(
        user_id=user_id,
        name=_('Enable Theme Animations'),
        value='admin_enable_theme_animation',
        content='effect',
        type='admin_theme',
        autoload='yes'
    )
    admin_enable_theme_animation.save()

    admin_hide_aside = Setting(
        user_id=user_id,
        name=_('Hide Aside In Menu'),
        value='admin_hide_aside',
        content='aside-hide',
        type='admin_theme',
        autoload='yes'
    )
    admin_hide_aside.save()

    admin_visible_aside = Setting(
        user_id=user_id,
        name=_('Visible Aside'),
        value='admin_visible_aside',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_visible_aside.save()

    admin_fixed_aside = Setting(
        user_id=user_id,
        name=_('Aside Fixed Position'),
        value='admin_fixed_aside',
        content='aside-fixed',
        type='admin_theme',
        autoload='yes'
    )
    admin_fixed_aside.save()

    admin_float_aside = Setting(
        user_id=user_id,
        name=_('Aside Fload'),
        value='admin_float_aside',
        content='aside-float',
        type='admin_theme',
        autoload='yes'
    )
    admin_float_aside.save()

    admin_left_aside = Setting(
        user_id=user_id,
        name=_('Aside Left Position'),
        value='admin_left_aside',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_left_aside.save()

    admin_dark_aside = Setting(
        user_id=user_id,
        name=_('Aside Dark Version'),
        value='admin_dark_aside',
        content='aside-bright',
        type='admin_theme',
        autoload='yes'
    )
    admin_dark_aside.save()

    admin_color_theme = Setting(
        user_id=user_id,
        name=_('Color Theme'),
        value='admin_color_theme',
        content='type-d/theme-dark.min.css',
        type='admin_theme',
        autoload='yes'
    )
    admin_color_theme.save()

    admin_boxed_layout = Setting(
        user_id=user_id,
        name=_('Admin Boxed Layout'),
        value='admin_boxed_layout',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_boxed_layout.save()

    admin_boxed_bg = Setting(
        user_id=user_id,
        name=_('Admin Boxed Background'),
        value='admin_boxed_bg',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_boxed_bg.save()
