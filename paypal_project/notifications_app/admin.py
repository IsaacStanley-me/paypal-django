from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'unread', 'created_at')
    list_filter = ('unread',)
    search_fields = ('user__email','message')
