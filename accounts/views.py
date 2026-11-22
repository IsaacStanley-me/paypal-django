from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.translation import activate, gettext as _
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import IntegrityError
import json
from django.urls import reverse
from django.conf import settings
import time
from .forms import (SignupDetailsForm, LoginForm, PhoneVerificationForm, AccountTypeForm, CountryForm)
from .models import User, Profile, ContactRequest, ChatSession, ChatMessage
from wallet.models import Wallet  # ✅ import your Wallet model
from .country_data import COUNTRIES_DATA, get_country_data, get_country_language, get_verification_code


def signup_step1(request):
    """Step 1: Account type selection"""
    if request.method == "POST":
        form = AccountTypeForm(request.POST)
        if form.is_valid():
            account_type = form.cleaned_data['account_type']
            request.session['signup_account_type'] = account_type
            return redirect('accounts:signup_email')
    else:
        form = AccountTypeForm()
    
    return render(request, "accounts/signup_step1.html", {"form": form})


def signup_country(request):
    """Step 3: Country selection"""
    if 'signup_email' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        country = request.POST.get('country')
        if country:
            request.session['signup_country'] = country
            
            # Determine language from country by default (no user selection UI)
            language = get_country_language(country)
            request.session['signup_language'] = language
            # If a user is already authenticated during signup resume, update their profile too
            if request.user.is_authenticated:
                try:
                    profile, _ = Profile.objects.get_or_create(user=request.user)
                    profile.country = country
                    profile.language = language
                    profile.save()
                except Exception:
                    pass
            
            return redirect('accounts:signup_phone')
    else:
        # Sort countries alphabetically
        sorted_countries = dict(sorted(COUNTRIES_DATA.items(), key=lambda x: x[1]['name']))
    
    return render(request, "accounts/signup_country_new.html", {
        "countries_data": sorted_countries,
    })


def signup_details(request):
    """Step 3: Details form"""
    if 'signup_country' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        form = SignupDetailsForm(request.POST)
        if form.is_valid():
            # Create user
            user = form.save()
            # Persist phone on the User and mark as verified (per requirement)
            try:
                user.phone = form.cleaned_data.get('phone')
                user.phone_verified = True
                user.save()
            except Exception:
                pass
            
            # Create or update profile
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'account_type': request.session.get('signup_account_type', 'personal'),
                    'country': request.session.get('signup_country', 'US'),
                    'language': request.session.get('signup_language', 'en'),
                    'phone': form.cleaned_data.get('phone'),
                    'date_of_birth': form.cleaned_data.get('date_of_birth'),
                    'address': form.cleaned_data.get('address'),
                }
            )
            
            if not created:
                # Update existing profile
                profile.account_type = request.session.get('signup_account_type', 'personal')
                profile.country = request.session.get('signup_country', 'US')
                profile.language = request.session.get('signup_language', 'en')
                profile.phone = form.cleaned_data.get('phone')
                profile.date_of_birth = form.cleaned_data.get('date_of_birth')
                profile.address = form.cleaned_data.get('address')
                profile.save()
            
            # Create wallet
            Wallet.objects.create(user=user, icici_balance=0.00, reward_balance=0.00)
            
            # Login user
            login(request, user)
            
            # Clear session data
            request.session.pop('signup_account_type', None)
            request.session.pop('signup_country', None)
            request.session.pop('signup_language', None)
            
            messages.success(request, 'Account created successfully!')
            return redirect('wallet:dashboard')
    else:
        form = SignupDetailsForm()
    
    return render(request, "accounts/signup_details.html", {
        "form": form,
        "account_type": request.session.get('signup_account_type', 'personal'),
        "country": request.session.get('signup_country', 'US'),
        "language": request.session.get('signup_language', 'en')
    })


def phone_verification_view(request):
    """Step 3: Phone verification"""
    if 'user_id' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            
            # Check if code is valid (111111 or 222222)
            if verification_code in ['111111', '222222']:
                user_id = request.session.get('user_id')
                user = User.objects.get(id=user_id)
                
                # Mark phone as verified
                user.phone_verified = True
                user.save()
                
                # Create wallet
                Wallet.objects.create(user=user, icici_balance=0.00, reward_balance=0.00)
                
                # Log in the user
                login(request, user)
                
                # Clear all session data
                request.session.pop('user_id', None)
                request.session.pop('phone', None)
                request.session.pop('account_type', None)
                request.session.pop('country', None)
                request.session.pop('language', None)
                request.session.pop('email', None)
                request.session.pop('username', None)
                request.session.pop('first_name', None)
                request.session.pop('last_name', None)
                
                messages.success(request, 'Account created successfully!')
                return redirect('wallet:dashboard')
            else:
                messages.error(request, 'Invalid verification code. Please use 111111 or 222222')
    else:
        form = PhoneVerificationForm()
    
    phone = request.session.get('phone', '')
    return render(request, "accounts/phone_verification.html", {
        "form": form,
        "phone": phone,
        "current_step": 2,
        "progress_width": 66
    })


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                # Apply user's saved language to session on login
                try:
                    profile = user.profile
                    if profile and getattr(profile, 'language', None):
                        request.session['django_language'] = profile.language
                        activate(profile.language)
                except Exception:
                    pass
                return redirect('/wallet/dashboard/')
            else:
                messages.error(request, "Invalid email or password")
        else:
            messages.error(request, "Invalid email or password")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')

@login_required
def settings_view(request):
    """Account settings page"""
    if request.method == 'POST':
        # Update user profile
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        
        # Handle profile picture upload with unique filename to bust caches
        if 'profile_picture' in request.FILES:
            uploaded = request.FILES['profile_picture']
            ts = int(time.time())
            base_name = getattr(uploaded, 'name', 'avatar.jpg')
            new_name = f"profile_pictures/{user.id}_{ts}_{base_name}"
            # Save with a new name; avoid immediate user.save() in save() call to keep subsequent field updates
            user.profile_picture.save(new_name, uploaded, save=False)
        
        user.save()
        
        # Update profile
        profile, created = Profile.objects.get_or_create(user=user)
        profile.date_of_birth = request.POST.get('date_of_birth') or None
        profile.address = request.POST.get('address', '')
        # Language selector removed; keep existing profile.language unchanged
        profile.save()
        
        # Persist currency preference in session (no model field required)
        selected_currency = request.POST.get('currency')
        if selected_currency:
            request.session['currency'] = selected_currency
        
        messages.success(request, 'Settings updated successfully!')
        # Redirect and set language cookie so preference sticks across requests
        next_url = request.POST.get('next') or reverse('accounts:settings')
        response = redirect(next_url)
        return response
    
    return render(request, 'accounts/settings.html', {
        'user': request.user,
        'current_currency': request.session.get('currency', 'USD'),
    })

@login_required
def security_view(request):
    """Security center page"""
    return render(request, 'accounts/security.html', {
        'user': request.user,
    })

@login_required
def security_activity(request):
    """Recent activity page (placeholder demo data)"""
    # Demo list; later can be replaced with real audit/activity logs
    activities = [
        {"icon": "fa-sign-in-alt", "class": "activity-login", "title": "Successful Login", "desc": "Logged in from Chrome on Windows", "time": "2 minutes ago"},
        {"icon": "fa-dollar-sign", "class": "activity-transaction", "title": "Transaction Completed", "desc": "Sent $50.00 to john@example.com", "time": "1 hour ago"},
        {"icon": "fa-key", "class": "activity-security", "title": "Password Changed", "desc": "Password was updated successfully", "time": "2 days ago"},
        {"icon": "fa-mobile-alt", "class": "activity-login", "title": "Mobile Login", "desc": "Logged in from PayPal Mobile App", "time": "3 days ago"},
        {"icon": "fa-credit-card", "class": "activity-transaction", "title": "Card Added", "desc": "New Visa card ending in 1234 was added", "time": "1 week ago"},
    ]
    return render(request, 'accounts/security_activity.html', {
        'activities': activities,
    })

@login_required
def change_password(request):
    """Allow a logged-in user to change their password securely"""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was changed successfully.')
            return redirect('accounts:security')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@require_POST
def verify_phone_quick(request):
    """Quickly mark the current user's phone as verified (for existing users)."""
    try:
        user = request.user
        if not user.phone:
            messages.error(request, 'Please add a phone number in Settings > Profile first.')
            return redirect('accounts:settings')
        user.phone_verified = True
        user.save(update_fields=['phone_verified'])
        messages.success(request, 'Phone number verified successfully!')
    except Exception as e:
        messages.error(request, f'Unable to verify phone: {e}')
    return redirect('accounts:security')

def signup_email(request):
    """Step 2: Email address"""
    if 'signup_account_type' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        email = request.POST.get('email')
        confirm_email = request.POST.get('confirm_email')
        
        if email != confirm_email:
            messages.error(request, 'Email addresses do not match')
            return render(request, 'accounts/signup_email.html', {"prefill_email": email, "prefill_confirm_email": confirm_email})
        
        # Prevent duplicate accounts by email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists. Please log in or use a different email.')
            return render(request, 'accounts/signup_email.html', {"prefill_email": email, "prefill_confirm_email": confirm_email})
        
        request.session['signup_email'] = email
        return redirect('accounts:signup_country')
    
    return render(request, 'accounts/signup_email.html')

def signup_phone(request):
    """Step 3: Phone number"""
    if 'signup_email' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        country = request.POST.get('country')
        phone = request.POST.get('phone')
        
        if not country or not phone:
            messages.error(request, 'Please select country and enter phone number')
            return render(request, 'accounts/signup_phone.html', {
                'countries_data': COUNTRIES_DATA
            })
        
        request.session['signup_country'] = country
        request.session['signup_phone'] = phone
        return redirect('accounts:signup_verification')
    
    # Sort countries alphabetically
    sorted_countries = dict(sorted(COUNTRIES_DATA.items(), key=lambda x: x[1]['name']))
    return render(request, 'accounts/signup_phone.html', {
        'countries_data': sorted_countries
    })

def signup_verification(request):
    """Step 4: Phone verification"""
    if 'signup_phone' not in request.session:
        return redirect('accounts:signup_step1')
    
    country = request.session.get('signup_country')
    phone = request.session.get('signup_phone')
    country_data = get_country_data(country)
    verification_code = get_verification_code(country)
    
    if request.method == "POST":
        entered_code = request.POST.get('verification_code')
        
        if entered_code == verification_code:
            request.session['phone_verified'] = True
            return redirect('accounts:signup_password')
        else:
            messages.error(request, 'Invalid verification code')
    
    return render(request, 'accounts/signup_verification.html', {
        'phone_display': f"{country_data['code']} {phone}",
        'verification_code': verification_code
    })

def signup_password(request):
    """Step 5: Create password"""
    if 'phone_verified' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'accounts/signup_password.html')
        
        request.session['signup_password'] = password
        return redirect('accounts:signup_personal_info')
    
    return render(request, 'accounts/signup_password.html')

def signup_personal_info(request):
    """Step 6: Personal information"""
    if 'signup_password' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        nationality = request.POST.get('nationality')
        date_of_birth = request.POST.get('date_of_birth')
        
        # Validate age (must be 16+)
        from datetime import datetime, date
        birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        if age < 16:
            messages.error(request, 'You must be at least 16 years old to create a PayPal account')
            return render(request, 'accounts/signup_personal_info.html', {
                'countries_data': COUNTRIES_DATA
            })
        
        request.session['signup_first_name'] = first_name
        request.session['signup_last_name'] = last_name
        request.session['signup_nationality'] = nationality
        request.session['signup_date_of_birth'] = date_of_birth
        
        account_type = request.session.get('signup_account_type')
        if account_type == 'business':
            return redirect('accounts:signup_business_info')
        else:
            return redirect('accounts:signup_address')
    
    # Sort countries alphabetically
    sorted_countries = dict(sorted(COUNTRIES_DATA.items(), key=lambda x: x[1]['name']))
    return render(request, 'accounts/signup_personal_info.html', {
        'countries_data': sorted_countries
    })

def signup_address(request):
    """Step 7: Address information (Personal)"""
    if 'signup_first_name' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2', '')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        state = request.POST.get('state')
        
        request.session['signup_address1'] = address1
        request.session['signup_address2'] = address2
        request.session['signup_city'] = city
        request.session['signup_postal_code'] = postal_code
        request.session['signup_state'] = state
        
        # Redirect to profile picture step
        return redirect('accounts:signup_profile_picture')
    
    return render(request, 'accounts/signup_address.html')

def signup_profile_picture(request):
    """Step 8: Profile picture (optional)"""
    if 'signup_first_name' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        profile_picture = request.FILES.get('profile_picture')
        # Do NOT store file objects in session (not JSON serializable). Pass directly.
        return create_user_account(reques
