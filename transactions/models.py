from django.db import models
from django.conf import settings
from django.utils import timezone

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('TRANSFER', 'Transfer'),
        ('WITHDRAW', 'Withdraw'),
        ('ADMIN_ADJUST', 'Admin Adjustment'),
        ('REWARD', 'Reward Credit'),
        ('REQUEST', 'Money Request'),
        ('SEND', 'Send Money'),
        ('RECEIVE', 'Receive Money'),
        ('DEPOSIT', 'Deposit'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('DECLINED', 'Declined'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    counterparty = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='counterparty_transactions')
    tx_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    # New fields for bank withdrawals
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_holder = models.CharField(max_length=100, blank=True, null=True)

    # Optional fields for card withdrawals
    card_brand = models.CharField(max_length=30, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_holder = models.CharField(max_length=100, blank=True, null=True)

    # International fee controls (admin editable)
    FEE_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
    ]
    international_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    international_fee_message = models.TextField(blank=True)
    international_fee_status = models.CharField(max_length=20, choices=FEE_STATUS_CHOICES, default='PENDING')

    # Voucher proof upload
    voucher_image = models.ImageField(upload_to='vouchers/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.tx_type} - {self.amount}"

    @property
    def is_pending(self):
        return self.status == 'PENDING'

    @property
    def fee_min_estimate(self):
        """10% of amount as minimum estimated fee."""
        from decimal import Decimal
        return (self.amount or Decimal('0')) * Decimal('0.10')

    @property
    def fee_max_estimate(self):
        """30% of amount as maximum estimated fee."""
        from decimal import Decimal
        return (self.amount or Decimal('0')) * Decimal('0.30')


class TransactionFeeNote(models.Model):
    """Stores each admin-provided international fee message as a separate note for a transaction."""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='fee_notes')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for TX #{self.transaction_id} at {self.created_at:%Y-%m-%d %H:%M}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.email}"
