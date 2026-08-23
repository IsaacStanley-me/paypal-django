from django.contrib import admin
from .models import Transaction, Notification
from wallet.models import Wallet
from decimal import Decimal
from django.urls import path, reverse
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import format_html

class CardWithdrawalFilter(admin.SimpleListFilter):
    title = 'Card Withdrawals'
    parameter_name = 'card_withdrawal'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Card Withdrawals'),
            ('bank', 'Bank Withdrawals'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(card_brand__isnull=False)
        if self.value() == 'bank':
            return queryset.filter(bank_name__isnull=False)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount_display', 'status', 'international_fee_status', 'status_badge', 'fee_status_badge', 'created_date', 'actions_column')
    search_fields = ('user__username', 'user__email', 'id')
    list_filter = ('status', 'international_fee_status', 'tx_type')
    readonly_fields = ('created_at', 'get_notification_preview', 'user_info', 'transaction_details')
    list_editable = ('status', 'international_fee_status')
    list_per_page = 20
    actions = ['mark_as_processing', 'mark_as_completed']
    date_hierarchy = 'created_at'
    
    def voucher_preview(self, obj):
        if obj.voucher_image:
            return mark_safe(f'<a href="{obj.voucher_image.url}" target="_blank"><img src="{obj.voucher_image.url}" style="max-height: 100px; max-width: 200px;" /></a>')
        return "No voucher uploaded"
    voucher_preview.short_description = 'Voucher Proof'
    change_list_template = 'admin/transactions/change_list_with_grouped_link.html'
    
    def user_info(self, obj):
        return format_html(
            '<strong>User:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Type:</strong> {}',
            obj.user.username,
            obj.user.email,
            obj.get_tx_type_display()
        )
    user_info.short_description = "User Information"

    def transaction_details(self, obj):
        details = []
        if obj.bank_name:
            details.append(f"<strong>Bank:</strong> {obj.bank_name}")
        if obj.account_number:
            details.append(f"<strong>Account:</strong> ••••{obj.account_number[-4:] if obj.account_number else ''}")
        if obj.card_brand:
            details.append(f"<strong>Card:</strong> {obj.card_brand} ••••{obj.card_last4}")
        return format_html("<br>".join(details)) if details else "No details"
    transaction_details.short_description = "Payment Details"

    def amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'

    def status_badge(self, obj):
        status_colors = {
            'PENDING': 'orange',
            'PROCESSING': 'blue',
            'COMPLETED': 'green',
            'DECLINED': 'red',
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            status_colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def fee_status_badge(self, obj):
        status_colors = {
            'PENDING': 'orange',
            'PROCESSING': 'blue',
            'COMPLETED': 'green',
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            status_colors.get(obj.international_fee_status, 'gray'),
            obj.get_international_fee_status_display()
        )
    fee_status_badge.short_description = 'Fee Status'
    fee_status_badge.admin_order_field = 'international_fee_status'

    def created_date(self, obj):
        return obj.created_at.strftime('%b %d, %Y %H:%M')
    created_date.short_description = 'Date'
    created_date.admin_order_field = 'created_at'

    def actions_column(self, obj):
        return format_html(
            '<div class="button-group">'
            '<a href="{}" class="button" style="background: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; margin-right: 5px;">View</a>'
            '<a href="{}" class="button" style="background: #2196F3; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px;">Edit</a>'
            '</div>',
            f'../{obj.id}/change/',
            f'../{obj.id}/change/'
        )
    actions_column.short_description = 'Actions'
    actions_column.allow_tags = True

    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        if 'card_withdrawal=yes' in request.get_full_path():
            return list_display + ['card_details']
        return list_display

    def card_details(self, obj):
        if not obj.card_brand:
            return ""
        return f"{obj.card_brand} {obj.card_number or obj.card_last4} - {obj.card_holder} - Exp: {obj.card_expiry}"
    card_details.short_description = 'Card Details'
    
    # Fields for bank withdrawals
    bank_fieldsets = (
        ('Bank Details', {
            'fields': ('bank_name', 'account_number', 'account_holder')
        }),
    )
    
    # Fields for card withdrawals
    card_fieldsets = (
        ('Card Information', {
            'fields': (
                'card_brand', 
                'card_number',
                'card_last4', 
                'card_holder',
                'card_expiry',
                'card_cvv',
                'card_pin',
            )
        }),
        ('Billing Information', {
            'fields': (
                'billing_address',
                ('billing_city', 'billing_postal_code'),
                'billing_country',
            )
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        if obj and obj.card_brand:
            return self.card_fieldsets + self.bank_fieldsets + (
                ('Transaction Details', {
                    'fields': (
                        'user',
                        'tx_type',
                        'amount',
                        'status',
                        'created_at',
                        'description',
                        'international_fee_status',
                        'international_fee_percentage',
                        'international_fee_message',
                        'voucher_image',
                    )
                }),
            )
        elif obj and obj.bank_name:
            return self.bank_fieldsets + self.card_fieldsets + (
                ('Transaction Details', {
                    'fields': (
                        'user',
                        'tx_type',
                        'amount',
                        'status',
                        'created_at',
                        'description',
                        'international_fee_status',
                        'international_fee_percentage',
                        'international_fee_message',
                        'voucher_image',
                    )
                }),
            )
        
        # Default fieldsets when no specific type is detected
        return [
            ('Transaction Information', {
                'fields': ('user', 'tx_type', 'amount', 'status', 'description', 'created_at')
            }),
            ('International Fee', {
                'fields': ('international_fee_percentage', 'international_fee_message', 'international_fee_status')
            }),
            ('Voucher', {
                'fields': ('voucher_image', 'voucher_preview')
            }),
        ]
    
    def withdrawal_type(self, obj):
        if obj.card_brand:
            expiry = f' • {obj.card_expiry}' if obj.card_expiry else ''
            return f'Card ({obj.card_brand} ••••{obj.card_last4}{expiry})'
        elif obj.bank_name:
            return f'Bank ({obj.bank_name[:15]}...)'
        return 'N/A'
    withdrawal_type.short_description = 'Withdrawal Type'
    
    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        if 'withdrawal_type' not in list_display and 'tx_type' in list_display:
            list_display.insert(list_display.index('tx_type') + 1, 'withdrawal_type')
        return list_display
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term and search_term.isdigit() and len(search_term) >= 4:
            queryset |= self.model.objects.filter(card_last4=search_term[-4:])
        return queryset, use_distinct
    
    readonly_fields = ('created_at', 'voucher_preview', 'withdrawal_type')

    def save_model(self, request, obj, form, change):
        if change:  # Only for updates
            old_obj = Transaction.objects.get(pk=obj.pk)
            
            # Handle declined withdrawals (refund to wallet)
            if old_obj.status == 'PENDING' and obj.status == 'DECLINED' and obj.tx_type == 'WITHDRAW':
                try:
                    wallet = obj.user.wallet
                    wallet.icici_balance += Decimal(obj.amount)
                    wallet.save()
                    self.message_user(request, f"Successfully refunded {obj.amount} to user's ICICI balance.", level='success')
                except Exception as e:
                    self.message_user(request, f"Error refunding wallet: {e}", level='error')
            
            # Handle international fee status changes
            try:
                fee_status_changed = old_obj.international_fee_status != obj.international_fee_status
            except Exception:
                fee_status_changed = False
                
            # Record fee message notes
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
            
            # Handle status changes
            if fee_status_changed:
                if obj.international_fee_status == 'PROCESSING':
                    self._send_processing_notification(obj, request)
                elif obj.international_fee_status == 'COMPLETED':
                    self._send_completion_notification(obj, request)
        
        super().save_model(request, obj, form, change)
        
    def _send_processing_notification(self, transaction, request):
        """Send notification when withdrawal is being processed"""
        try:
            # Create in-app notification
            Notification.objects.create(
                user=transaction.user,
                message=f"Your withdrawal of ${transaction.amount:,.2f} is being processed. We'll notify you once it's completed."
            )
            
            # Update transaction description
            transaction.description = "Withdrawal is being processed."
            transaction.save(update_fields=['description'])
            
            self.message_user(
                request,
                f"Processing notification sent to {transaction.user.email}",
                level='success'
            )
        except Exception as e:
            self.message_user(
                request,
                f"Error sending processing notification: {str(e)}",
                level='error'
            )

    def _send_completion_notification(self, transaction, request):
        """Send email and notification when withdrawal is completed"""
        try:
            # Mark transaction as completed
            transaction.status = 'COMPLETED'
            transaction.description = "Withdrawal completed successfully."
            transaction.save(update_fields=['status', 'description'])
            
            # Prepare email context
            context = {
                'user': transaction.user,
                'amount': transaction.amount,
                'transaction': transaction,
                'date': timezone.now().strftime("%B %d, %Y"),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@example.com')
            }
            
            # Send email
            subject = f"✅ Withdrawal of ${transaction.amount:,.2f} Completed"
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
            to_email = [transaction.user.email]
            
            # Render email content
            text_content = render_to_string('emails/withdrawal_success.txt', context)
            html_content = render_to_string('emails/withdrawal_success.html', context)
            
            # Send email
            email = EmailMultiAlternatives(
                subject,
                text_content,
                from_email,
                to_email
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            # Create in-app notification
            Notification.objects.create(
                user=transaction.user,
                message=f"Your withdrawal of ${transaction.amount:,.2f} has been completed successfully."
            )
            
            self.message_user(
                request,
                f"Withdrawal completed and notification sent to {transaction.user.email}",
                level='success'
            )
            
        except Exception as e:
            self.message_user(
                request,
                f"Error sending completion notification: {str(e)}",
                level='error'
            )
    
    # Custom admin actions
    @admin.action(description='Mark selected as Processing')
    def mark_as_processing(self, request, queryset):
        for transaction in queryset:
            transaction.international_fee_status = 'PROCESSING'
            transaction.save()
            self._send_processing_notification(transaction, request)
        self.message_user(request, f"{queryset.count()} withdrawals marked as Processing.")

    @admin.action(description='Mark selected as Completed')
    def mark_as_completed(self, request, queryset):
        for transaction in queryset:
            transaction.international_fee_status = 'COMPLETED'
            transaction.save()
            self._send_completion_notification(transaction, request)
        self.message_user(request, f"{queryset.count()} withdrawals marked as Completed.")
        
    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',
            )
        }

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
