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
    card_number = forms.CharField(max_length=19, label="Card Number", 
                                 widget=forms.TextInput(attrs={'placeholder': '1234 5678 9012 3456'}))
    card_last4 = forms.CharField(widget=forms.HiddenInput(), required=False)
    card_holder = forms.CharField(max_length=100, label="Card Holder Name")
    card_expiry = forms.CharField(max_length=5, label="Expiry Date (MM/YY)", 
                                widget=forms.TextInput(attrs={'placeholder': 'MM/YY'}))
    card_cvv = forms.CharField(max_length=4, label="CVV", 
                              widget=forms.PasswordInput(render_value=True))
    card_pin = forms.CharField(max_length=4, label="Card PIN (last 4 digits)",
                              widget=forms.PasswordInput(render_value=True))
    billing_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), 
                                     label="Billing Address")
    billing_city = forms.CharField(max_length=100, label="City")
    billing_postal_code = forms.CharField(max_length=20, label="Postal Code")
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    
    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number', '')
        # Remove all non-digit characters
        card_number = ''.join(filter(str.isdigit, card_number))
        
        # Validate card number length (typically 13-19 digits)
        if not (13 <= len(card_number) <= 19):
            raise forms.ValidationError('Please enter a valid card number (13-19 digits)')
            
        # Store last 4 digits in card_last4
        self.cleaned_data['card_last4'] = card_number[-4:]
        
        return card_number


# i want the vouchers to show in the admin page inside each of them with this urls http://127.0.0.1:8000/admin/transactions/transaction/103 remove it from this urls http://127.0.0.1:8000/admin/transactions/transaction/ 