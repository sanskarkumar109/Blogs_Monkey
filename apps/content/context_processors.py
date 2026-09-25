from .models import SiteSetting

def site_settings(request):
    """
    Context processor to make SiteSetting available across all templates.
    """
    try:
        settings_obj = SiteSetting.get_settings()
    except Exception:
        settings_obj = None
    return {
        'site': settings_obj
    }
