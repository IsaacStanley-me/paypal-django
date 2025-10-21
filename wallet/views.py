from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Wallet, LinkedCard, BankAccount
from transactions.models import Transaction, Notification
from .forms import LinkedCardForm, AddCardForm, BankAccountForm

@login_required
def dashboard(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:5]
    linked_cards = LinkedCard.objects.filter(user=request.user)
    bank_accounts = BankAccount.objects.filter(user=request.user)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return render(request, 'wallet/dashboard.html', {
        'wallet': wallet,
        'transactions': recent_transactions,
        'linked_cards': linked_cards,
        'bank_accounts': bank_accounts,
        'notifications': notifications,
        'notifications_count': notifications_count,
    })


@login_required
def wallet_dashboard(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    cards = LinkedCard.objects.filter(user=request.user)
    bank_accounts = BankAccount.objects.filter(user=request.user)

    # Add new card
    if request.method == "POST":
        form = LinkedCardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.user = request.user
            card.save()
            messages.success(request, "Card added successfully!")
            messages.info(request, "Your Bank will now be VERIFIED by the ADMIN Briefly")
            return redirect('wallet:wallet_dashboard')
    else:
        form = LinkedCardForm()

    return render(request, 'wallet/wallet.html', {
        'wallet': wallet,
        'cards': cards,
        'bank_accounts': bank_accounts,
        'form': form,
    })

@login_required
def add_card(request):
    if request.method == 'POST':
        form = AddCardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.user = request.user
            card.save()
            messages.success(request, "Card added successfully!")
            return redirect('wallet:wallet_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    return redirect('wallet:wallet_dashboard')

@login_required
def card_detail(request, pk):
    card = get_object_or_404(LinkedCard, pk=pk, user=request.user)
    return render(request, 'wallet/card_detail.html', {'card': card})

@login_required
def delete_card(request, pk):
    card = get_object_or_404(LinkedCard, pk=pk, user=request.user)
    card.delete()
    messages.success(request, "Card deleted successfully.")
    return redirect('wallet:dashboard')

@login_required
def upgrade_card(request, pk):
    card = get_object_or_404(LinkedCard, pk=pk, user=request.user)
    if request.method == 'POST':
        card.expiry_date = request.POST.get('expiry_date')
        card.street = request.POST.get('street')
        card.save()
        messages.success(request, "Card updated successfully!")
        return redirect('wallet:wallet_dashboard')
    return render(request, 'wallet/upgrade_card.html', {'card': card})

# Bank Account Management
@login_required
def bank_accounts(request):
    bank_accounts = BankAccount.objects.filter(user=request.user)
    return render(request, 'wallet/bank_accounts.html', {
        'bank_accounts': bank_accounts,
    })

@login_required
def add_bank_account(request):
    if request.method == 'POST':
        form = BankAccountForm(request.POST)
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.user = request.user
            bank_account.save()
            messages.success(request, "Bank account added successfully!")
            messages.info(request, "Your Bank will now be VERIFIED by the ADMIN Briefly")
            return redirect('wallet:bank_accounts')
        else:
            messages.error(request, "Please correct the errors below.")
    return redirect('wallet:bank_accounts')

@login_required
def delete_bank_account(request, pk):
    bank_account = get_object_or_404(BankAccount, pk=pk, user=request.user)
    bank_account.delete()
    messages.success(request, "Bank account removed successfully.")
    return redirect('wallet:bank_accounts')

@login_required
def verify_bank_account(request, pk):
    bank_account = get_object_or_404(BankAccount, pk=pk, user=request.user)
    if request.method == 'POST':
        # In a real app, you'd verify with the bank
        bank_account.is_verified = True
        bank_account.save()
        messages.success(request, "Bank account verified successfully!")
    return redirect('wallet:bank_accounts')

@login_required
def edit_bank_account(request, pk):
    bank_account = get_object_or_404(BankAccount, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BankAccountForm(request.POST, instance=bank_account)
        if form.is_valid():
            form.save()
            messages.success(request, "Bank account updated successfully!")
            return redirect('wallet:bank_accounts')
        else:
            messages.error(request, "Please correct the errors below.")
            return redirect('wallet:bank_accounts')
    return redirect('wallet:bank_accounts')
