from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.notifications_list, name='notifications_list'),
    path('read/<int:note_id>/', views.mark_read, name='notifications_mark_read'),
]
