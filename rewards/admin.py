from django.contrib import admin
from django.contrib import messages
from decimal import Decimal
from .models import RewardAccount, RewardTransaction, RewardConversionSettings, RewardActivityType, RewardActivityLog
from wallet.models import Wallet


@admin.register(RewardConversionSettings)
class RewardConversionSettingsAdmin(admin.ModelAdmin):
    list_display = ('activation_fee', 'conversion_rate', 'pay_to_email', 'updated_at')


@admin.register(RewardAccount)
class RewardAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'activation_paid', 'activation_paid_at', 'total_converted_amount')
    search_fields = ('user__email',)


@admin.register(RewardTransaction)
class RewardTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tx_type', 'status', 'points', 'amount', 'blocks', 'fee_amount', 'payout_account', 'created_at')
    list_filter = ('tx_type', 'status', 'created_at')
    search_fields = ('user__email', 'description')
    actions = ['approve_conversions', 'apply_earn_transactions', 'mark_declined']

    def save_model(self, request, obj, form, change):
        """When an admin manually marks a CONVERT tx as COMPLETED, apply wallet/account updates.
        Avoid double-apply by only acting when transitioning from a non-COMPLETED status to COMPLETED.
        """
        prev_status = None
        if change and obj.pk:
            try:
                prev_status = RewardTransaction.objects.get(pk=obj.pk).status
            except RewardTransaction.DoesNotExist:
                prev_status = None

        if obj.tx_type == 'CONVERT' and obj.status == 'COMPLETED' and prev_status != 'COMPLETED':
            try:
                account, _ = RewardAccount.objects.get_or_create(user=obj.user)
                if account.points < obj.points:
                    messages.error(request, "Not enough points to complete conversion; leaving status unchanged.")
                    # Revert status change
                    obj.status = prev_status or 'PENDING'
                else:
                    account.points -= obj.points
                    account.total_converted_amount = (account.total_converted_amount or Decimal('0')) + (obj.amount or Decimal('0'))
                    account.save()

                    wallet, _ = Wallet.objects.get_or_create(user=obj.user)
                    wallet.reward_balance = (wallet.reward_balance or Decimal('0')) + (obj.amount or Decimal('0'))
                    wallet.save()
            except Exception as e:
                messages.error(request, f"Error applying conversion completion: {e}")

        super().save_model(request, obj, form, change)

    def approve_conversions(self, request, queryset):
        """Approve pending conversion requests: deduct points and credit reward balance"""
        count_ok = 0
        count_skip = 0
        for tx in queryset.filter(tx_type='CONVERT', status='PENDING'):
            try:
                account, _ = RewardAccount.objects.get_or_create(user=tx.user)
                if account.points < tx.points:
                    count_skip += 1
                    continue
                # Deduct points
                account.points -= tx.points
                account.total_converted_amount = (account.total_converted_amount or Decimal('0')) + (tx.amount or Decimal('0'))
                account.save()
                # Credit wallet reward balance
                wallet, _ = Wallet.objects.get_or_create(user=tx.user)
                wallet.reward_balance = (wallet.reward_balance or Decimal('0')) + (tx.amount or Decimal('0'))
                wallet.save()
                # Mark completed
                tx.status = 'COMPLETED'
                tx.save()
                count_ok += 1
            except Exception:
                count_skip += 1
        self.message_user(request, f"Approved {count_ok} conversion(s); skipped {count_skip}.")
    approve_conversions.short_description = "Approve selected conversions"

    def apply_earn_transactions(self, request, queryset):
        """Apply pending EARN transactions to add points to user accounts"""
        count_ok = 0
        count_skip = 0
        for tx in queryset.filter(tx_type='EARN', status='PENDING'):
            try:
                account, _ = RewardAccount.objects.get_or_create(user=tx.user)
                account.points += abs(int(tx.points or 0))
                account.save()
                tx.status = 'COMPLETED'
                tx.save()
                count_ok += 1
            except Exception:
                count_skip += 1
        self.message_user(request, f"Applied {count_ok} earn transaction(s); skipped {count_skip}.")
    apply_earn_transactions.short_description = "Apply selected EARN transactions"

    def mark_declined(self, request, queryset):
        updated = queryset.update(status='DECLINED')
        self.message_user(request, f"Marked {updated} transaction(s) as declined.")
    mark_declined.short_description = "Mark selected as Declined"


@admin.register(RewardActivityType)
class RewardActivityTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'points', 'frequency', 'claimable', 'active')
    list_filter = ('frequency', 'claimable', 'active')
    search_fields = ('code', 'name')


@admin.register(RewardActivityLog)
class RewardActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'points', 'created_at')
    list_filter = ('activity', 'created_at')
    search_fields = ('user__email', 'activity__code', 'activity__name')

from django.contrib import admin

# Register your models here.
