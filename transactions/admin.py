from django.contrib import admin
from .models import Transaction
from wallet.models import Wallet
from decimal import Decimal
from django.urls import path, reverse
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tx_type', 'amount', 'status', 'created_at')
    list_filter = ('status', 'tx_type')
    search_fields = ('user__username', 'user__email')
    change_list_template = 'admin/transactions/change_list_with_grouped_link.html'
    
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
                    wallet.paypal_balance += Decimal(obj.amount)
                    wallet.save()
                except Exception as e:
                    self.message_user(request, f"Error refunding wallet: {e}", level='error')
        
        super().save_model(request, obj, form, change)

    # Custom URLs
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('grouped-by-user/', self.admin_site.admin_view(self.grouped_by_user_view), name='transactions_grouped_by_user'),
            path('grouped-by-user/<int:user_id>/', self.admin_site.admin_view(self.grouped_by_user_detail_view), name='transactions_grouped_by_user_detail'),
        ]
        return custom_urls + urls

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
