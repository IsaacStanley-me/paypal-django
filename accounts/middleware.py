from django.utils.deprecation import MiddlewareMixin
from django.utils import translation, timezone
from django.contrib.auth import logout
from django.contrib import messages

class LanguageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Check if user has a language preference in session
        if 'django_language' in request.session:
            language = request.session['django_language']
            translation.activate(language)
            request.LANGUAGE_CODE = language


class InactivityLogoutMiddleware(MiddlewareMixin):
    """Logs out authenticated users after 5 minutes of inactivity."""
    TIMEOUT_SECONDS = 300

    def process_request(self, request):
        if not request.user.is_authenticated:
            return
        now_ts = timezone.now().timestamp()
        last = request.session.get('last_activity_ts')
        request.session['last_activity_ts'] = now_ts
        if last is None:
            return
        try:
            idle = now_ts - float(last)
        except (TypeError, ValueError):
            return
        if idle > self.TIMEOUT_SECONDS:
            logout(request)
            messages.info(request, "You’ve been logged out for security reasons. Please log in again.")











