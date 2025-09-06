from django.utils.translation import gettext_lazy as _


# from ..data import load_general_setting_stores, load_theme_setting_stores, load_themes_stores

def load_admin_theme_setting_stores(model, user_id):
    Setting = model

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

    admin_navbar_show_usermenu = Setting(
        user_id=user_id,
        name=_('Navbar Show User Menu'),
        value='admin_navbar_show_usermenu',
        content='nav-user-menu',
        type='admin_theme',
        autoload='yes'
    )
    admin_navbar_show_usermenu.save()

    admin_navbar_show_menu = Setting(
        user_id=user_id,
        name=_('Navbar Show Menu'),
        value='admin_navbar_show_menu',
        content='',
        type='admin_theme',
        autoload='yes'
    )
    admin_navbar_show_menu.save()

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
