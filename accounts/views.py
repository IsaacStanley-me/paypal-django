from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import activate
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
            Wallet.objects.create(user=user, paypal_balance=0.00, reward_balance=0.00)
            
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
                Wallet.objects.create(user=user, paypal_balance=0.00, reward_balance=0.00)
                
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
        return create_user_account(request, profile_picture=profile_picture)
    
    return render(request, 'accounts/signup_profile_picture.html')

def signup_business_info(request):
    """Step 7: Business information"""
    if 'signup_first_name' not in request.session:
        return redirect('accounts:signup_step1')
    
    if request.method == "POST":
        business_name = request.POST.get('business_name')
        business_type = request.POST.get('business_type')
        business_location = request.POST.get('business_location')
        business_address = request.POST.get('business_address')
        business_website = request.POST.get('business_website', '')
        
        request.session['signup_business_name'] = business_name
        request.session['signup_business_type'] = business_type
        request.session['signup_business_location'] = business_location
        request.session['signup_business_address'] = business_address
        request.session['signup_business_website'] = business_website
        
        # Redirect to profile picture step
        return redirect('accounts:signup_profile_picture')
    
    return render(request, 'accounts/signup_business_info.html')

def create_user_account(request, profile_picture=None):
    """Create the user account with all collected information"""
    try:
        # Create user
        email = request.session.get('signup_email')
        password = request.session.get('signup_password')
        first_name = request.session.get('signup_first_name')
        last_name = request.session.get('signup_last_name')
        phone = request.session.get('signup_phone')
        country = request.session.get('signup_country')
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            phone_verified=True
        )
        
        # Handle profile picture if provided (use unique filename to avoid caching issues)
        if profile_picture:
            ts = int(time.time())
            base_name = getattr(profile_picture, 'name', 'avatar.jpg')
            new_name = f"profile_pictures/{user.id}_{ts}_{base_name}"
            user.profile_picture.save(new_name, profile_picture, save=False)
            user.save(update_fields=['profile_picture'])
        
        # Create profile
        profile = Profile.objects.create(
            user=user,
            account_type=request.session.get('signup_account_type', 'personal'),
            country=country,
            language=get_country_language(country),
            date_of_birth=request.session.get('signup_date_of_birth'),
            address=f"{request.session.get('signup_address1', '')} {request.session.get('signup_address2', '')}".strip()
        )
        
        # Create wallet
        Wallet.objects.create(user=user, paypal_balance=0.00, reward_balance=0.00)
        
        # Login user
        login(request, user)
        
        # Clear session data
        for key in list(request.session.keys()):
            if key.startswith('signup_'):
                del request.session[key]
        
        messages.success(request, 'Account created successfully!')
        return redirect('wallet:dashboard')
        
    except IntegrityError:
        # Duplicate username/email at creation time (safety net)
        messages.error(request, 'This email is already registered. Please log in or use a different email.')
        return redirect('accounts:signup_email')
    except Exception as e:
        # Keep the user on the last step to correct issues instead of resetting the flow
        messages.error(request, f'Error creating account: {str(e)}')
        return redirect('accounts:signup_profile_picture')

def contact_us_view(request):
    """Handle contact form submissions"""
    if request.method == 'POST':
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Create contact request
        contact_request = ContactRequest.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
            contact_type='form'
        )
        
        # If user is authenticated, automatically create a pending live chat and redirect to chat page
        redirect_url = None
        try:
            if request.user.is_authenticated:
                chat_session = ChatSession.objects.create(
                    user=request.user,
                    subject=f"Support: {subject or 'General'}",
                    status='pending'
                )
                # Initial message
                ChatMessage.objects.create(
                    chat_session=chat_session,
                    sender=request.user,
                    message=message or 'User requested support via contact form.'
                )
                # Notify user
                try:
                    from transactions.models import Notification
                    Notification.objects.create(
                        user=request.user,
                        message="Your live chat request was received. An agent will be with you soon."
                    )
                except Exception:
                    pass
                redirect_url = reverse('accounts:chat_page')
        except Exception:
            pass
        
        return JsonResponse({
            'status': 'success',
            'message': 'Thank you for your message! We will get back to you within 24 hours.',
            'redirect_url': redirect_url
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def admin_contact_management(request):
    """Admin interface for managing contact requests"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('wallet:dashboard')
    
    contact_requests = ContactRequest.objects.all()
    staff_users = User.objects.filter(is_staff=True)
    non_staff_users = User.objects.filter(is_staff=False)
    
    if request.method == 'POST':
        contact_id = request.POST.get('contact_id')
        action = request.POST.get('action')
        
        try:
            contact = ContactRequest.objects.get(id=contact_id)
            
            if action == 'assign':
                assigned_to_id = request.POST.get('assigned_to')
                if assigned_to_id:
                    contact.assigned_to_id = assigned_to_id
                    contact.status = 'in_progress'
                    contact.save()
                    messages.success(request, f'Contact request assigned successfully.')
            
            elif action == 'resolve':
                admin_response = request.POST.get('admin_response')
                contact.admin_response = admin_response
                contact.status = 'resolved'
                contact.resolved_at = timezone.now()
                contact.save()
                messages.success(request, f'Contact request marked as resolved.')
            
            elif action == 'close':
                contact.status = 'closed'
                contact.save()
                messages.success(request, f'Contact request closed.')
                
        except ContactRequest.DoesNotExist:
            messages.error(request, 'Contact request not found.')
    
    return render(request, 'accounts/admin_contact_management.html', {
        'contact_requests': contact_requests,
        'staff_users': staff_users,
        'non_staff_users': non_staff_users,
    })

def start_live_chat(request):
    """Start a live chat session"""
    if request.method == 'POST':
        # Get or create user for chat
        email = request.POST.get('email')
        first_name = request.POST.get('firstName', 'Chat User')
        last_name = request.POST.get('lastName', '')
        message = request.POST.get('message', 'User wants to start a live chat')
        
        # Try to find existing user by email, or create a temporary one
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create a temporary user for the chat
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password='temp_password_123'  # Temporary password
            )
        
        # Create chat session (pending assignment)
        chat_session = ChatSession.objects.create(
            user=user,
            subject='Live Chat Request',
            status='pending'
        )
        
        # Create initial message
        ChatMessage.objects.create(
            chat_session=chat_session,
            sender=user,
            message=message
        )
        # Notify user
        try:
            from transactions.models import Notification
            Notification.objects.create(
                user=user,
                message="Your live chat request was received. An agent will be with you soon."
            )
        except Exception:
            pass
        
        return JsonResponse({
            'status': 'success',
            'message': 'Live chat request submitted! An agent will be assigned to you shortly.',
            'chat_id': chat_session.id,
            'redirect_url': reverse('accounts:chat_page')
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def admin_chat_management(request):
    """Admin interface for managing chat sessions"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('wallet:dashboard')
    
    chat_sessions = ChatSession.objects.all()
    staff_users = User.objects.filter(is_staff=True)
    non_staff_users = User.objects.filter(is_staff=False)
    all_users = User.objects.all()
    
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        action = request.POST.get('action')
        
        try:
            chat = ChatSession.objects.get(id=chat_id) if chat_id else None
            
            if action == 'assign':
                agent_id = request.POST.get('agent_id')
                if agent_id:
                    agent = User.objects.get(id=agent_id)
                    chat.agent = agent
                    chat.status = 'active'
                    chat.started_at = timezone.now()
                    chat.save()
                    
                    # Create notifications for user and agent
                    from transactions.models import Notification
                    Notification.objects.create(
                        user=chat.user,
                        message=f"Agent {agent.first_name} {agent.last_name} has been assigned to your chat. Click 'Chats' to begin. [chat:{chat.id}]"
                    )
                    Notification.objects.create(
                        user=agent,
                        message=f"You have been assigned to assist {chat.user.first_name or chat.user.email}. Click 'Chat now' to start. [chat:{chat.id}]"
                    )
                    
                    messages.success(request, f'Chat assigned to {agent.first_name} {agent.last_name}.')
            elif action == 'reassign_user':
                user_id = request.POST.get('user_id')
                if user_id:
                    new_user = User.objects.get(id=user_id)
                    old_user = chat.user
                    chat.user = new_user
                    chat.save()
                    from transactions.models import Notification
                    Notification.objects.create(
                        user=new_user,
                        message="You have been assigned to a live chat. Click 'Chats' to start."
                    )
                    if old_user and old_user != new_user:
                        Notification.objects.create(
                            user=old_user,
                            message="Your live chat user assignment was changed by an admin."
                        )
                    messages.success(request, 'Chat user reassigned successfully.')
            
            elif action == 'close':
                chat.status = 'closed'
                chat.save()
                messages.success(request, f'Chat session closed.')
            
            elif action == 'create_chat':
                # Create a new chat with selected customer and optional agent
                customer_id = request.POST.get('customer_id')
                agent_id = request.POST.get('agent_id')
                subject = request.POST.get('subject') or 'Live Chat'
                init_message = request.POST.get('init_message') or 'Admin started a chat.'
                if not customer_id:
                    messages.error(request, 'Please select a customer user.')
                else:
                    customer = User.objects.get(id=customer_id)
                    chat = ChatSession.objects.create(
                        user=customer,
                        subject=subject,
                        status='pending'
                    )
                    if agent_id:
                        agent = User.objects.get(id=agent_id)
                        chat.agent = agent
                        chat.status = 'active'
                        chat.started_at = timezone.now()
                        chat.save()
                    ChatMessage.objects.create(chat_session=chat, sender=customer if not agent_id else (User.objects.get(id=agent_id)), message=init_message)
                    from transactions.models import Notification
                    Notification.objects.create(user=customer, message='A new live chat was created for you. Click \"Chats\" to begin.')
                    if agent_id:
                        Notification.objects.create(user=agent, message=f'You have been assigned to assist {customer.first_name or customer.email}.')
                    messages.success(request, 'New chat created successfully.')
        
        except ChatSession.DoesNotExist:
            messages.error(request, 'Chat session not found.')
    
    return render(request, 'accounts/admin_chat_management.html', {
        'chat_sessions': chat_sessions,
        'staff_users': staff_users,
        'non_staff_users': non_staff_users,
        'all_users': all_users,
    })

@login_required
def chat_page(request):
    """Chat page for users and agents"""
    # Get user's chat sessions
    from django.db.models import Q
    if request.user.is_staff:
        # Staff: assigned active chats
        chat_sessions = ChatSession.objects.filter(agent=request.user, status='active')
    else:
        # Non-staff: chats where user is requester (active or pending) OR is assigned agent (active)
        chat_sessions = ChatSession.objects.filter(
            Q(user=request.user, status__in=['active', 'pending']) | Q(agent=request.user, status='active')
        )
    
    # Pending indicator for users
    has_pending = False
    if not request.user.is_staff:
        has_pending = ChatSession.objects.filter(user=request.user, status='pending').exists()
    
    return render(request, 'accounts/chat_page.html', {
        'chat_sessions': chat_sessions,
        'has_pending': has_pending,
    })

@login_required
def agent_join_chat(request, chat_id):
    """Agent confirms joining a chat; notify the user and redirect to chat page"""
    try:
        chat = ChatSession.objects.get(id=chat_id)
        # Allow assigned agent to join, whether staff or not
        if chat.agent != request.user:
            messages.error(request, 'Access denied.')
            return redirect('wallet:dashboard')
        # Notify user that agent is ready
        try:
            from transactions.models import Notification
            Notification.objects.create(
                user=chat.user,
                message="Your agent is ready to talk. Click 'Chats' to start."
            )
        except Exception:
            pass
    except ChatSession.DoesNotExist:
        messages.error(request, 'Chat session not found.')
        return redirect('wallet:dashboard')
    return redirect('accounts:chat_page')

@login_required
def send_chat_message(request):
    """Send a chat message"""
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        message = request.POST.get('message')
        
        try:
            chat = ChatSession.objects.get(id=chat_id)
            
            # Check if user is part of this chat
            if request.user != chat.user and request.user != chat.agent:
                return JsonResponse({'status': 'error', 'message': 'Access denied'})
            
            # Create message
            chat_message = ChatMessage.objects.create(
                chat_session=chat,
                sender=request.user,
                message=message
            )
            
            return JsonResponse({
                'status': 'success',
                'message_id': chat_message.id,
                'timestamp': chat_message.timestamp.strftime('%H:%M')
            })
            
        except ChatSession.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Chat not found'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def get_chat_messages(request, chat_id):
    """Get chat messages for a specific chat"""
    try:
        chat = ChatSession.objects.get(id=chat_id)
        
        # Check if user is part of this chat
        if request.user != chat.user and request.user != chat.agent:
            return JsonResponse({'status': 'error', 'message': 'Access denied'})
        
        messages = chat.messages.all()
        messages_data = []
        
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'sender': msg.sender.first_name or msg.sender.email,
                'message': msg.message,
                'timestamp': msg.timestamp.strftime('%H:%M'),
                'is_own': msg.sender == request.user
            })
        
        return JsonResponse({
            'status': 'success',
            'messages': messages_data
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Chat not found'})
