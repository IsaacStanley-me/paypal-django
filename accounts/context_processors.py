from django.utils import translation

def language_context(request):
    """Add language information to template context"""
    return {
        'current_language': translation.get_language(),
        'language_code': translation.get_language(),
    }