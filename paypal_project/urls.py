from django.contrib import admin
from django.urls import path, include
from home import views as home_views
from django.views.generic.base import RedirectView
from django.templatetags.static import static
from django.conf import settings
from django.conf.urls.static import static as media_static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_views.index, name='home'),
    # Serve favicon at /favicon.ico to avoid 404s
    path('favicon.ico', RedirectView.as_view(url=static('images/paypal-logo.png'), permanent=True)),

    # ✅ Correct way — wrap include() in a tuple with app_name
    path('accounts/', include('accounts.urls')),  # ✅ this line is key
    path('wallet/', include(('wallet.urls', 'wallet'), namespace='wallet')),
    path('transactions/', include('transactions.urls')),
    path('rewards/', include('rewards.urls')),
    
    # Support pages
    path('support/help/', home_views.help_center, name='help_center'),
    path('support/contact/', home_views.contact_us, name='contact_us'),
    path('support/security/', home_views.security_center, name='security_center'),
    path('support/disputes/', home_views.dispute_resolution, name='dispute_resolution'),
    path('support/accessibility/', home_views.accessibility, name='accessibility'),

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += media_static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
