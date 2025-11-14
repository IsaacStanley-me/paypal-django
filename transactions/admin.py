from django.contrib import admin
from .models import Transaction
from wallet.models import Wallet
from decimal import Decimal
from django.urls import path, reverse
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.utils.safestring import mark_safe

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tx_type', 'amount', 'status', 'international_fee_status', 'created_at')
    list_filter = ('status', 'tx_type')
    search_fields = ('user__username', 'user__email')
    change_list_template = 'admin/transactions/change_list_with_grouped_link.html'
    fields = (
        'user', 'tx_type', 'amount', 'status', 'description', 'created_at',
        'bank_name', 'account_number', 'account_holder',
        'international_fee_percentage', 'international_fee_message', 'international_fee_status',
        'voucher_image', 'voucher_preview',
    )
    readonly_fields = ('created_at', 'voucher_preview',)

    def save_model(self, request, obj, form, change):
        """
        Automatically handle refunds when a withdrawal is declined.
        """
        if change:  # only if updating an existing transaction
            old_obj = Transaction.objects.get(pk=obj.pk)

            # Check if status changed from PENDING -> DECLINED
            if old_obj.status == 'PENDING' and obj.status == 'DECLINED' and obj.tx_type == 'WITHDRAW':
                try:
                    wallet = obj.user.wallet
                    # Use icici_balance instead of paypal_balance
                    wallet.icici_balance += Decimal(obj.amount)
                    wallet.save()
                    self.message_user(request, f"Successfully refunded {obj.amount} to user's ICICI balance.", level='success')
                except Exception as e:
                    self.message_user(request, f"Error refunding wallet: {e}", level='error')

            # Handle international fee workflow admin controls
            try:
                fee_status_changed = old_obj.international_fee_status != obj.international_fee_status
            except Exception:
                fee_status_changed = False

            # Record a fee message note whenever the admin changes the message to a non-empty value
            try:
                msg_changed = (old_obj.international_fee_message or '') != (obj.international_fee_message or '')
            except Exception:
                msg_changed = False
            if msg_changed and (obj.international_fee_message or '').strip():
                try:
                    from .models import TransactionFeeNote
                    TransactionFeeNote.objects.create(transaction=obj, message=obj.international_fee_message.strip())
                except Exception as e:
                    self.message_user(request, f"Error saving fee note: {e}", level='error')

            # Always send a PROCESSING notification on save while status is PROCESSING
            if obj.international_fee_status == 'PROCESSING':
                try:
                    from .models import Notification
                    Notification.objects.create(
                        user=obj.user,
                        message=(
                            "Your international payment process has been updated. Check your payment page for the latest instructions. "
                            f"[fee_tx:{obj.id}]"
                        )
                    )
                except Exception as e:
                    self.message_user(request, f"Error creating notification: {e}", level='error')

            # If set to COMPLETED, auto-complete withdrawal and send email
            if obj.international_fee_status == 'COMPLETED':
                try:
                    # Mark transaction completed if it was pending
                    if obj.tx_type == 'WITHDRAW' and obj.status != 'COMPLETED':
                        obj.status = 'COMPLETED'
                    # Send email via Gmail SMTP
                    from django.template.loader import render_to_string
                    from django.core.mail import EmailMultiAlternatives
                    context = {
                        'user': obj.user,
                        'transaction': obj,
                    }
                    subject = "✅ Withdrawal Successful — ICICI Bank"
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
                    to_emails = [obj.user.email]
                    text_body = render_to_string('emails/withdrawal_success.txt', context)
                    html_body = render_to_string('emails/withdrawal_success.html', context)
                    email = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to_emails)
                    email.attach_alternative(html_body, "text/html")
                    email.send()
                    # Notify user in-app as well
                    try:
                        from .models import Notification
                        Notification.objects.create(
                            user=obj.user,
                            message=(
                                "Your withdrawal has been completed successfully. You can now view the transaction details. "
                                f"[fee_tx:{obj.id}]"
                            )
                        )
                    except Exception:
                        pass
                except Exception as e:
                    self.message_user(request, f"Error sending completion email: {e}", level='error')

        super().save_model(request, obj, form, change)

    # Custom URLs
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('grouped-by-user/', self.admin_site.admin_view(self.grouped_by_user_view), name='transactions_grouped_by_user'),
            path('grouped-by-user/<int:user_id>/', self.admin_site.admin_view(self.grouped_by_user_detail_view), name='transactions_grouped_by_user_detail'),
        ]
        return custom_urls + urls

    def voucher_preview(self, obj):
        try:
            if obj.voucher_image and hasattr(obj.voucher_image, 'url'):
                return mark_safe(f'<img src="{obj.voucher_image.url}" style="max-height:160px;border-radius:6px;" />')
        except Exception:
            return ""
        return ""
    voucher_preview.short_description = "Voucher Image"
    voucher_preview.allow_tags = True

    # List view: grouped by user with counts and search
    def grouped_by_user_view(self, request):
        User = get_user_model()
        q = (request.GET.get('q') or '').strip()
        base = Transaction.objects.all()
        if q:
            base = base.filter(Q(user__username__icontains=q) | Q(user__email__icontains=q))
        grouped = (
            base.values('user_id', 'user__username', 'user__email')
                .annotate(
                    total=Count('id'),
                    pending=Count('id', filter=Q(status='PENDING')),
                    completed=Count('id', filter=Q(status='COMPLETED')),
                )
                .order_by('-total')
        )
        context = dict(
            self.admin_site.each_context(request),
            title='Transactions Grouped by User',
            grouped=grouped,
            query=q,
            opts=self.model._meta,
        )
        return render(request, 'admin/transactions/grouped_by_user.html', context)

    # Detail view: transactions for a specific user
    def grouped_by_user_detail_view(self, request, user_id: int):
        User = get_user_model()
        user = get_object_or_404(User, id=user_id)
        txs = (Transaction.objects
               .filter(user_id=user_id)
               .select_related('user')
               .order_by('-created_at'))
        context = dict(
            self.admin_site.each_context(request),
            title=f"Transactions for {user.email or user.username}",
            user_obj=user,
            transactions=txs,
            opts=self.model._meta,
        )
        return render(request, 'admin/transactions/grouped_by_user_detail.html', context)
