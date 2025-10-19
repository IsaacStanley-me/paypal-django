from django.db import models
from django.conf import settings

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    paypal_balance = models.DecimalField(max_digits=19, decimal_places=2, default=0.00)
    reward_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.email} Wallet"

class LinkedCard(models.Model):
    CARD_TYPES = [
        ('Visa', 'Visa'),
        ('MasterCard', 'MasterCard'),
        ('Verve', 'Verve'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    card_number = models.CharField(max_length=16)
    expiry_date = models.CharField(max_length=5)  # e.g. '12/27'
    street = models.CharField(max_length=255, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def masked_number(self):
        return f"**** **** **** {self.card_number[-4:]}"
    
    def __str__(self):
        return f"{self.card_type} ending {self.card_number[-4:]}"

class BankAccount(models.Model):
    ACCOUNT_TYPES = [
        ('checking', 'Checking'),
        ('savings', 'Savings'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    routing_number = models.CharField(max_length=9)
    account_number = models.CharField(max_length=20)
    account_holder_name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    def masked_account_number(self):
        return f"****{self.account_number[-4:]}"
    
    def masked_routing_number(self):
        return f"{self.routing_number[:4]}****"
    
    def __str__(self):
        return f"{self.bank_name} - {self.masked_account_number()}"
