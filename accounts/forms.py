from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Profile

class AccountTypeForm(forms.Form):
    ACCOUNT_TYPE_CHOICES = [
        ('personal', 'Personal Account'),
        ('business', 'Business Account'),
    ]
    
    account_type = forms.ChoiceField(
        choices=ACCOUNT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'account-type-radio'}),
        label='Choose your account type'
    )

class CountryForm(forms.Form):
    COUNTRY_CHOICES = [
        ('US', '🇺🇸 United States'),
        ('CA', '🇨🇦 Canada'),
        ('GB', '🇬🇧 United Kingdom'),
        ('DE', '🇩🇪 Germany'),
        ('FR', '🇫🇷 France'),
        ('ES', '🇪🇸 Spain'),
        ('IT', '🇮🇹 Italy'),
        ('AU', '🇦🇺 Australia'),
        ('JP', '🇯🇵 Japan'),
        ('BR', '🇧🇷 Brazil'),
        ('MX', '🇲🇽 Mexico'),
        ('IN', '🇮🇳 India'),
        ('CN', '🇨🇳 China'),
    ]
    
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select your country'
    )

class SignupDetailsForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '+1 (555) 123-4567'}),
        help_text='Enter your phone number'
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your address'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone', 'password1', 'password2')

class PhoneVerificationForm(forms.Form):
    verification_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 6-digit code',
            'maxlength': '6'
        }),
        help_text='Use code: 111111 or 222222'
    )

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')
