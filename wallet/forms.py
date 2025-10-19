from django import forms
from .models import LinkedCard, BankAccount

class LinkedCardForm(forms.ModelForm):
    class Meta:
        model = LinkedCard
        fields = ['card_type', 'card_number', 'expiry_date', 'street']
        widgets = {
            'card_number': forms.TextInput(attrs={'placeholder': 'Enter 16-digit card number'}),
            'expiry_date': forms.TextInput(attrs={'placeholder': 'MM/YY'}),
            'street': forms.TextInput(attrs={'placeholder': 'Billing address'}),
        }

class AddCardForm(forms.ModelForm):
    class Meta:
        model = LinkedCard
        fields = ['card_type', 'card_number', 'expiry_date', 'street']
        widgets = {
            'card_type': forms.Select(attrs={'class': 'form-control'}),
            'card_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 16-digit card number'}),
            'expiry_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MM/YY'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Billing address'}),
        }

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'account_type', 'routing_number', 'account_number', 'account_holder_name', 'address']
        widgets = {
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank name'
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'routing_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter 9-digit routing number',
                'maxlength': '9'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account number'
            }),
            'account_holder_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account holder full name'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Bank address (optional)',
                'rows': 3
            }),
        }
    
    def clean_routing_number(self):
        routing_number = self.cleaned_data.get('routing_number')
        if routing_number and len(routing_number) != 9:
            raise forms.ValidationError("Routing number must be exactly 9 digits.")
        return routing_number
    
    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if account_number and len(account_number) < 4:
            raise forms.ValidationError("Account number must be at least 4 digits.")
        return account_number
