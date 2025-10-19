from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.http import JsonResponse

@login_required
def notifications_list(request):
    notes = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    data = [{"id": n.id, "message": n.message, "unread": n.unread, "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S")} for n in notes]
    return JsonResponse({"notifications": data})

@login_required
def mark_read(request, note_id):
    n = get_object_or_404(Notification, id=note_id, user=request.user)
    n.unread = False
    n.save()
    return JsonResponse({"ok": True})
