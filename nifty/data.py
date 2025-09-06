from django.utils.translation import gettext_lazy as _

from .models import Setting


# from ..data import load_general_setting_stores, load_theme_setting_stores, load_themes_stores

def load_admin_setting_stores(user_id=None):
    # Setting = apps.get_model("nifty", "Setting")

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
        content='/static/niftyv2/img/favicon.png',
        type='admin',
        autoload='yes'
    )

    admin_site_favicon.save()

    admin_site_logo = Setting(
        user_id=user_id,
        name=_('Logo'),
        value='admin_site_logo',
        content='/static/niftyv2/img/logo.png',
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
    # Setting = apps.get_model("nifty", "Setting")

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
    # Setting = apps.get_model("nifty", "Setting")

    admin_colpase_menu = Setting(
        user_id=user_id,
        name=_('Navigation Collapsed Mode'),
        value='admin_colpase_menu',
        content='mn--max',
        type='admin_theme',
        autoload='yes'
    )
    admin_colpase_menu.save()

    admin_navbar_fixed = Setting(
        user_id=user_id,
        name=_('Navbar Fixed Position'),
        value='admin_navbar_fixed',
        content='mn--sticky',
        type='admin_theme',
        autoload='yes'
    )
    admin_navbar_fixed.save()

    admin_theme_animation = Setting(
        user_id=user_id,
        name=_('Theme Animations'),
        value='admin_theme_animation',
        content='out-back',
        type='admin_theme',
        autoload='yes'
    )
    admin_theme_animation.save()

    admin_color_theme = Setting(
        user_id=user_id,
        name=_('Color Theme'),
        value='admin_color_theme',
        content='navy',
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
        content='/static/niftyv2/premium/boxed-bg/abstract/bg/9.jpg',
        type='admin_theme',
        autoload='yes'
    )
    admin_boxed_bg.save()

    admin_color_modes = Setting(
        user_id=user_id,
        name=_('Admin Color Modes'),
        value='admin_color_modes',
        content='light',
        type='admin_theme',
        autoload='yes'
    )
    admin_color_modes.save()

    admin_header_fixed = Setting(
        user_id=user_id,
        name=_('Header Fixed Position'),
        value='admin_header_fixed',
        content='hd--sticky',
        type='admin_theme',
        autoload='yes'
    )
    admin_header_fixed.save()

    admin_layout_color_mode = Setting(
        user_id=user_id,
        name=_('Layout Color Mode'),
        value='admin_layout_color_mode',
        content='tm--full-hd',
        type='admin_theme',
        autoload='yes'
    )
    admin_layout_color_mode.save()

    admin_font_size = Setting(
        user_id=user_id,
        name=_('Admin Font Size'),
        value='admin_font_size',
        content='16',
        type='admin_theme',
        autoload='yes'
    )
    admin_font_size.save()

    admin_sidebar_mode = Setting(
        user_id=user_id,
        name=_('Admin Sidebar mode'),
        value='admin_sidebar_mode',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_sidebar_mode.save()

    admin_sidebar_show = Setting(
        user_id=user_id,
        name=_('Admin Sidebar Show'),
        value='admin_sidebar_show',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_sidebar_show.save()

    admin_pinned_sidebar = Setting(
        user_id=user_id,
        name=_('Admin Pinned Sidebar'),
        value='admin_pinned_sidebar',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_pinned_sidebar.save()

    admin_unite_sidebar = Setting(
        user_id=user_id,
        name=_('Admin Unite Sidebar'),
        value='admin_unite_sidebar',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_unite_sidebar.save()

    admin_stuck_sidebar = Setting(
        user_id=user_id,
        name=_('Admin Stuck Sidebar'),
        value='admin_stuck_sidebar',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_stuck_sidebar.save()

    admin_static_sidebar = Setting(
        user_id=user_id,
        name=_('Admin Static position'),
        value='admin_static_sidebar',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_static_sidebar.save()

    admin_bd_sidebar = Setting(
        user_id=user_id,
        name=_('Admin Disable backdrop'),
        value='admin_bd_sidebar',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_bd_sidebar.save()

    admin_sdh_btn = Setting(
        user_id=user_id,
        name=_('Admin Hide sidebar button'),
        value='admin_sdh_btn',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_sdh_btn.save()
