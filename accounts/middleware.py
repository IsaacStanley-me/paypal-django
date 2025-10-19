from django.utils.deprecation import MiddlewareMixin
from django.utils import translation

class LanguageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Check if user has a language preference in session
        if 'django_language' in request.session:
            language = request.session['django_language']
            translation.activate(language)
            request.LANGUAGE_CODE = language











