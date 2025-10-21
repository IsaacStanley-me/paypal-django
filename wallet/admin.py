from django.contrib import admin
from .models import Wallet, LinkedCard, BankAccount

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'paypal_balance', 'reward_balance')
    search_fields = ('user__email',)


@admin.register(LinkedCard)
class LinkedCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_type', 'masked_number_admin', 'security_code', 'expiry_date', 'added_at')
    list_filter = ('card_type', 'added_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('added_at', 'security_code')

    def masked_number_admin(self, obj):
        return obj.masked_number()
    masked_number_admin.short_description = 'Card Number'


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'bank_name', 'account_type', 'masked_account_admin', 'masked_routing_admin',
        'is_verified', 'created_at', 'verified_at'
    )
    list_filter = ('account_type', 'is_verified', 'created_at')
    search_fields = ('user__email', 'user__username', 'bank_name')
    readonly_fields = ('created_at', 'verified_at')
    actions = ['mark_verified']

    def masked_account_admin(self, obj):
        return obj.masked_account_number()
    masked_account_admin.short_description = 'Account Number'

    def masked_routing_admin(self, obj):
        return obj.masked_routing_number()
    masked_routing_admin.short_description = 'Routing Number'

    def mark_verified(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for acct in queryset:
            if not acct.is_verified:
                acct.is_verified = True
                if not acct.verified_at:
                    acct.verified_at = timezone.now()
                acct.save()
                updated += 1
        self.message_user(request, f"Marked {updated} bank account(s) as verified.")
    mark_verified.short_description = 'Mark selected bank accounts as verified'
