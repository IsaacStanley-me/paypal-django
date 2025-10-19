from django.contrib import admin
from .models import Wallet

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'paypal_balance', 'reward_balance')
    search_fields = ('user__email',)
