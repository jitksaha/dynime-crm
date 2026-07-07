"""
Context processors for the Horilla application.

Provides sidebar, company, language, recently viewed items, notifications,
and menu context for templates.
"""

from django.conf import settings
from django.utils.translation import get_language
from django.core.cache import cache

from dynime.contrib.core.models import Company, RecentlyViewed
from dynime.contrib.notifications.models import (
    Notification,
    NotificationSoundPreference,
)
from dynime.menu.floating_menu import get_floating_menu
from dynime.menu.main_section_menu import get_main_section_menu
from dynime.menu.my_settings_menu import get_my_settings_menu
from dynime.menu.settings_menu import get_settings_menu
from dynime.menu.sub_section_menu import get_sub_section_menu
from dynime.utils.branding import load_branding


def company_list(request):
    """Return all available companies, cached for 5 minutes."""
    companies = cache.get("available_companies")
    if companies is None:
        companies = list(Company.objects.all())
        cache.set("available_companies", companies, 300)
    return {"available_companies": companies}


def allowed_languages(request):
    """
    Return only languages defined in ALLOWED_LANGUAGES.
    """
    return {
        "allowed_languages": [
            {
                "code": code,
                "name": name,
                "flag": flag,
                "active": (code == get_language()),
            }
            for code, name, flag in settings.ALLOWED_LANGUAGES
        ]
    }


def recently_viewed_items(request):
    """
    Return the user's 6 most recently viewed items, cleaning invalid references.
    """
    if request.user.is_authenticated:
        cache_key = f"recently_viewed_user_{request.user.id}"
        items = cache.get(cache_key)
        if items is None:
            items = []
            for rv in RecentlyViewed.objects.filter(user=request.user).order_by(
                "-viewed_at"
            )[:6]:
                try:
                    if rv.content_object:
                        items.append(rv)
                except Exception:
                    rv.delete()
            cache.set(cache_key, items, 60) # Cache for 1 minute
        return {"recently_viewed_items": items}
    return {}


def unread_notifications(request):
    """Return unread notifications and sound preference for the current user."""
    if request.user.is_authenticated:
        cache_key = f"unread_notifications_user_{request.user.id}"
        cached_data = cache.get(cache_key)
        if cached_data is None:
            try:
                sound_muted = request.user.notification_sound_preference.sound_muted
            except NotificationSoundPreference.DoesNotExist:
                sound_muted = False
            
            # Since notifications change, we convert the queryset to a list to cache it,
            # and cache for a very short period (e.g. 15 seconds) to keep it real-time.
            unread = list(Notification.objects.filter(
                user=request.user, read=False
            ).order_by("-created_at"))
            
            cached_data = {
                "unread_notifications": unread,
                "notification_sound_muted": sound_muted,
            }
            cache.set(cache_key, cached_data, 15)
        return cached_data
    return {}


def menu_context_processor(request):
    """Return context for various menus, cached for 5 minutes per user/app/section."""
    current_app_label = (
        request.resolver_match.app_name if request.resolver_match else None
    )
    section_param = request.GET.get("section")
    
    user_id = request.user.id if request.user.is_authenticated else "anonymous"
    cache_key = f"user_menus_{user_id}_{current_app_label}_{section_param}"
    
    menus = cache.get(cache_key)
    if menus is None:
        menus = {
            "main_section_menu": get_main_section_menu(request),
            "sub_section_menu": get_sub_section_menu(request),
            "settings_menu": get_settings_menu(request),
            "floating_menu": get_floating_menu(request),
            "my_settings_menu": get_my_settings_menu(request),
        }
        cache.set(cache_key, menus, 300)

    return {
        **menus,
        "current_section": section_param,
        "current_app_label": current_app_label,
    }


def currency_context(request):
    """
    Add currency information to all templates automatically, cached per user.
    """
    if not request.user.is_authenticated:
        return {}

    from dynime.contrib.core.models import MultipleCurrency

    user_id = request.user.id
    cache_key = f"user_currency_{user_id}"
    user_currency = cache.get(cache_key)
    if user_currency is None:
        user_currency = MultipleCurrency.get_user_currency(request.user)
        cache.set(cache_key, user_currency, 300)

    default_currency = None
    if hasattr(request.user, "company") and request.user.company:
        company_id = request.user.company.id
        default_cache_key = f"default_currency_company_{company_id}"
        default_currency = cache.get(default_cache_key)
        if default_currency is None:
            default_currency = MultipleCurrency.get_default_currency(request.user.company)
            cache.set(default_cache_key, default_currency, 300)

    return {
        "user_currency": user_currency,
        "default_currency": default_currency,
    }


def branding(request):
    """
    Django context processor function that return
    dictionary containing branding configuration values such as
    TITLE, LOGIN_WELCOME_LINE, LOGO_PATH, etc.
    """
    # Branding configuration is static but we can cache it for 10 minutes to avoid file operations
    branding_data = cache.get("branding_data")
    if branding_data is None:
        branding_data = load_branding()
        cache.set("branding_data", branding_data, 600)
    return branding_data
