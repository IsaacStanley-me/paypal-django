from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('support/help/', views.help_center, name='help_center'),
    path('support/contact/', views.contact_us, name='contact_us'),
    path('support/security/', views.security_center, name='security_center'),
    path('support/disputes/', views.dispute_resolution, name='dispute_resolution'),
    path('support/accessibility/', views.accessibility, name='accessibility'),
]
