from django.db import models
from django.conf import settings


class RewardConversionSettings(models.Model):
    """Admin-configured settings for reward conversion"""
    activation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0.0100)  # $ per point
    pay_to_email = models.EmailField(help_text="Email account where activation fee should be paid")
    # Block-based conversion (e.g., every 100 points -> $20 payout, $5 fee)
    points_per_block = models.PositiveIntegerField(default=100)
    payout_per_block = models.DecimalField(max_digits=10, decimal_places=2, default=20)
    fee_per_block = models.DecimalField(max_digits=10, decimal_places=2, default=5)
    payout_account_number = models.CharField(max_length=255, blank=True, help_text="Account number/name to receive conversion fees")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rewards Settings (fee={self.activation_fee}, rate={self.conversion_rate})"


class RewardAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reward_account')
    points = models.PositiveIntegerField(default=0)
    activation_paid = models.BooleanField(default=False)
    activation_paid_at = models.DateTimeField(null=True, blank=True)
    total_converted_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} Rewards (points={self.points})"


class RewardTransaction(models.Model):
    TX_TYPES = (
        ('EARN', 'Earned Points'),
        ('CONVERT', 'Converted to Cash'),
        ('ACTIVATION', 'Activation Fee Marked Paid'),
    )
    STATUS = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('DECLINED', 'Declined'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reward_transactions')
    tx_type = models.CharField(max_length=16, choices=TX_TYPES)
    status = models.CharField(max_length=16, choices=STATUS, default='COMPLETED')
    points = models.IntegerField(default=0, help_text="Points involved (use positive value for requested conversion)")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monetary amount for conversion or activation")
    # Conversion metadata
    blocks = models.PositiveIntegerField(default=0)
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payout_account = models.CharField(max_length=255, blank=True, help_text="Destination account/email for payout if applicable")
    receipt_reference = models.CharField(max_length=255, blank=True, help_text="Reference the user paid fee with (screenshot/ref)")
    receipt_image = models.ImageField(upload_to='reward_receipts/', blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} {self.tx_type} points={self.points} amount={self.amount}"


class RewardActivityType(models.Model):
    """Catalog of reward activities users can complete to earn points"""
    FREQ_CHOICES = (
        ('ONCE', 'One-time only'),
        ('DAILY', 'Once per day'),
        ('UNLIMITED', 'Unlimited'),
    )
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=0)
    frequency = models.CharField(max_length=16, choices=FREQ_CHOICES, default='ONCE')
    claimable = models.BooleanField(default=True, help_text='If false, awarded programmatically (e.g., referral)')
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (+{self.points})"


class RewardActivityLog(models.Model):
    """Logs when users earn points by activities"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reward_activity_logs')
    activity = models.ForeignKey(RewardActivityType, on_delete=models.CASCADE, related_name='logs')
    points = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} did {self.activity.code} (+{self.points})"
