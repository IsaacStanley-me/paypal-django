from django import forms

class TransferForm(forms.Form):
    recipient_email = forms.EmailField()
    amount = forms.DecimalField(decimal_places=2, max_digits=12)
from django import forms

class BankWithdrawForm(forms.Form):
    bank_name = forms.CharField(max_length=100)
    account_number = forms.CharField(max_length=50)
    account_holder = forms.CharField(max_length=100)
    amount = forms.DecimalField(max_digits=12, decimal_places=2)

class CardWithdrawForm(forms.Form):
    card_brand = forms.CharField(max_length=30, label="Card Brand (e.g., Visa, MasterCard)")
    card_last4 = forms.CharField(max_length=4, label="Card Last 4 Digits")
    card_holder = forms.CharField(max_length=100, label="Card Holder Name")
    amount = forms.DecimalField(max_digits=12, decimal_places=2)
