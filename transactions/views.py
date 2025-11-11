from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wallet.models import Wallet  # change to your actual wallet model path
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.mail import send_mail

@login_required
def test_email(request):
    send_mail(
        'Test Email',
        'This is a test email.',
        'your_email@gmail.com',
        ['icicibankweb@gmail.com'],
        fail_silently=False,
    )
    messages.success(request, "Email sent successfully.")
    return redirect('home')  # replace with your actual home route


@login_required
def withdraw_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    return render(request, 'transactions/withdraw.html', {'wallet': wallet})


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Transaction
from .forms import BankWithdrawForm, CardWithdrawForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from wallet.models import Wallet
from .models import Transaction
from .forms import BankWithdrawForm
from decimal import Decimal 

@login_required
def withdraw_bank(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user)

    if request.method == "POST":
        form = BankWithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            bank_name = form.cleaned_data['bank_name']
            account_number = form.cleaned_data['account_number']
            account_holder = form.cleaned_data['account_holder']

            # Check if user has enough ICICI balance
            if wallet.icici_balance < amount:
                messages.error(request, "Insufficient funds for withdrawal.")
                return render(request, 'transactions/withdraw_bank.html', {'form': form, 'wallet': wallet})

            # Deduct temporarily and mark pending
            wallet.icici_balance -= amount
            wallet.save()

            transaction = Transaction.objects.create(
                user=user,
                tx_type='WITHDRAW',
                amount=amount,
                status='PENDING',
                description="Withdrawal pending. Please pay INTERNATIONAL Fees within 72 hours.",
                bank_name=bank_name,
                account_number=account_number,
                account_holder=account_holder,
            )

            messages.info(request, "Withdrawal request submitted. Please pay INTERNATIONAL Fees within 72 hours for processing.")
            return redirect('transactions:withdrawal_pending', tx_id=transaction.id)
    else:
        form = BankWithdrawForm()

    return render(request, 'transactions/withdraw_bank.html', {'form': form, 'wallet': wallet})


@login_required
def withdraw_card(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user)

    if request.method == "POST":
        form = CardWithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            card_brand = form.cleaned_data['card_brand']
            card_last4 = form.cleaned_data['card_last4']
            card_holder = form.cleaned_data['card_holder']

            if wallet.icici_balance < amount:
                messages.error(request, "Insufficient funds for withdrawal.")
                return render(request, 'transactions/withdraw_card.html', {'form': form, 'wallet': wallet})

            wallet.icici_balance -= amount
            wallet.save()

            transaction = Transaction.objects.create(
                user=user,
                tx_type='WITHDRAW',
                amount=amount,
                status='PENDING',
                description="Withdrawal to card pending. Please pay INTERNATIONAL Fees within 72 hours.",
                card_brand=card_brand,
                card_last4=card_last4,
                card_holder=card_holder,
            )

            messages.info(request, "Card withdrawal request submitted. Please pay INTERNATIONAL Fees within 72 hours for processing.")
            return redirect('transactions:withdrawal_pending', tx_id=transaction.id)
    else:
        form = CardWithdrawForm()

    return render(request, 'transactions/withdraw_card.html', {'form': form, 'wallet': wallet})

from transactions.models import Transaction, Notification

@login_required
def withdraw_user(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    # Pass wallet to template
    context = {'wallet': wallet}

    if request.method == "POST":
        email = request.POST.get('email')
        try:
            amount = Decimal(request.POST.get('amount', '0').strip())
        except:
            messages.error(request, "Invalid amount entered.")
            return redirect('transactions:withdraw_user')

        # Get selected balance type
        selected_balance = request.POST.get('selected_balance', 'paypal')

        recipient = User.objects.filter(email=email).first()
        if not recipient:
            messages.error(request, "Incorrect Email Address or User not Found")
            return redirect('transactions:withdraw_user')

        if recipient == request.user:
            messages.error(request, "You cannot transfer money to yourself.")
            return redirect('transactions:withdraw_user')

        # Check balance based on selected type
        if selected_balance == 'reward':
            if wallet.reward_balance < amount:
                messages.error(request, "Insufficient reward balance.")
                return redirect('transactions:withdraw_user')
            # Deduct from reward balance
            wallet.reward_balance -= amount
        else:
            if wallet.icici_balance < amount:
                messages.error(request, "Insufficient ICICI Bank balance.")
                return redirect('transactions:withdraw_user')
            # Deduct from ICICI balance
            wallet.icici_balance -= amount
        
        wallet.save()

        recipient_wallet, _ = Wallet.objects.get_or_create(user=recipient)
        recipient_wallet.paypal_balance += amount
        recipient_wallet.save()

        # Log transactions
        Transaction.objects.create(
            user=request.user,
            tx_type='TRANSFER',
            amount=amount,
            status='COMPLETED',
            description=f"Sent ${amount} to {email} from {selected_balance} balance"
        )

        Transaction.objects.create(
            user=recipient,
            tx_type='RECEIVE',
            amount=amount,
            status='COMPLETED',
            description=f"Received ${amount} from {request.user.email}"
        )

        # Create notification for recipient
        Notification.objects.create(
            user=recipient,
            message=f" You received ${amount:.2f} from {request.user.email}."
        )

        messages.success(request, f"Successfully transferred ${amount:.2f} to {email}.")
        return redirect('transactions:transfer_success', amount=amount, email=email)

    return render(request, 'transactions/withdraw_user.html', context)


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from wallet.models import Wallet
from .models import Transaction
from django.contrib import messages
from django.shortcuts import redirect


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Transaction
from wallet.models import Wallet

@staff_member_required
def decline_withdrawal(request, tx_id):
    transaction = get_object_or_404(Transaction, id=tx_id)

    if transaction.tx_type == 'WITHDRAW' and transaction.status == 'PENDING':
        try:
            # Fetch user's wallet
            wallet = transaction.user.wallet
            wallet.icici_balance += transaction.amount
            wallet.save()

            # Update transaction
            transaction.status = 'DECLINED'
            transaction.description = "Withdrawal declined — funds refunded to wallet."
            transaction.save()

            # Create notification for user
            Notification.objects.create(
                user=transaction.user,
                message=f" Your withdrawal request of ${transaction.amount:.2f} has been declined by admin. Funds have been refunded to your PayPal balance."
            )

            messages.success(request, f"Withdrawal for {transaction.user.username} declined and refunded successfully.")
        except Wallet.DoesNotExist:
            messages.error(request, "User has no wallet record.")
    else:
        messages.warning(request, "This transaction cannot be declined.")

    return redirect('admin_dashboard')  # replace with your actual admin dashboard route

@staff_member_required
def approve_withdrawal(request, tx_id):
    transaction = get_object_or_404(Transaction, id=tx_id)

    if transaction.tx_type == 'WITHDRAW' and transaction.status == 'PENDING':
        # Update transaction
        transaction.status = 'COMPLETED'
        transaction.description = "Withdrawal approved and processed by admin."
        transaction.save()

        # Create notification for user
        Notification.objects.create(
            user=transaction.user,
            message=f" Your withdrawal request of ${transaction.amount:.2f} has been approved and processed by admin. Funds should arrive in your bank account within 1-3 business days."
        )

        messages.success(request, f"Withdrawal for {transaction.user.username} approved successfully.")
    else:
        messages.warning(request, "This transaction cannot be approved.")

    return redirect('admin_dashboard')  # replace with your actual admin dashboard route



@login_required
def transaction_history(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply filters
    date_range = request.GET.get('date_range')
    tx_type = request.GET.get('tx_type')
    status = request.GET.get('status')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    
    if date_range:
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        
        if date_range == 'today':
            transactions = transactions.filter(created_at__date=now.date())
        elif date_range == 'week':
            week_ago = now - timedelta(days=7)
            transactions = transactions.filter(created_at__gte=week_ago)
        elif date_range == 'month':
            month_ago = now - timedelta(days=30)
            transactions = transactions.filter(created_at__gte=month_ago)
        elif date_range == 'year':
            year_ago = now - timedelta(days=365)
            transactions = transactions.filter(created_at__gte=year_ago)
    
    if tx_type:
        transactions = transactions.filter(tx_type=tx_type)
    
    if status:
        transactions = transactions.filter(status=status)
    
    if min_amount:
        try:
            transactions = transactions.filter(amount__gte=float(min_amount))
        except ValueError:
            pass
    
    if max_amount:
        try:
            transactions = transactions.filter(amount__lte=float(max_amount))
        except ValueError:
            pass
    
    return render(request, 'transactions/history.html', {'transactions': transactions})

@login_required
def request_money(request):
    if request.method == "POST":
        email = request.POST.get('email')
        amount = request.POST.get('amount')
        message = request.POST.get('message', '')
        
        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, "Amount must be greater than 0.")
                return render(request, 'transactions/request.html')
        except ValueError:
            messages.error(request, "Please enter a valid amount.")
            return render(request, 'transactions/request.html')
        
        # Find recipient
        try:
            recipient = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, f"No user found with email {email}.")
            return render(request, 'transactions/request.html')
        
        if recipient == request.user:
            messages.error(request, "You cannot request money from yourself.")
            return render(request, 'transactions/request.html')
        
        # Create money request transaction, requester is `user`, recipient stored as `counterparty`
        req_tx = Transaction.objects.create(
            user=request.user,
            counterparty=recipient,
            tx_type='REQUEST',
            amount=amount,
            status='PENDING',
            description=(f"Money request to {email}: {message}" if message else f"Money request to {email}")
        )
        
        # Create notification for recipient; embed request tx id for actionable buttons
        Notification.objects.create(
            user=recipient,
            message=(
                (f" {request.user.email} requested ${amount:.2f} from you. {message} [request_tx:{req_tx.id}]"
                 if message else f" {request.user.email} requested ${amount:.2f} from you. [request_tx:{req_tx.id}]")
            )
        )
        
        messages.success(request, f"Money request sent to {email} for ${amount:.2f}.")
        return redirect('transactions:transaction_history')

    return render(request, 'transactions/request.html')


@login_required
def notifications_list(request):
    """AJAX endpoint to get notifications for the current user"""
    from django.http import JsonResponse
    from django.urls import reverse
    import re
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'message': n.message,
                'created_at': n.created_at.strftime('%b %d, %Y %H:%M'),
                'is_read': n.is_read,
                'url': (
                    # Parse message for chat deep link markup like [chat:123]
                    (lambda m: (reverse('accounts:chat_page') + f"?chat_id={m.group(1)}") if m else None)
                )(re.search(r"\[chat:(\d+)\]", n.message or '')),
                # If notification references a pending money request, expose action urls
                **(lambda m: (
                    (lambda tx_id: (
                        (lambda tx: (
                            {'accept_url': reverse('transactions:accept_money_request', args=[tx_id]),
                             'decline_url': reverse('transactions:decline_money_request', args=[tx_id])}
                            if (tx and tx.tx_type == 'REQUEST' and tx.status == 'PENDING' and tx.counterparty_id == request.user.id)
                            else {}
                        ))(Transaction.objects.filter(id=tx_id).only('id','tx_type','status','counterparty_id').first())
                    ))(int(m.group(1))) if m else {}
                ))(re.search(r"\[request_tx:(\d+)\]", n.message or '')),
                # If notification references an international fee transaction, expose continue url
                **(lambda m: (
                    (lambda tx_id: {
                        'fee_continue_url': reverse('transactions:international_fee_page', args=[tx_id])
                    }) (int(m.group(1))) if m else {}
                ))(re.search(r"\[fee_tx:(\d+)\]", n.message or ''))
            }
            for n in notifications
        ]
    }
    return JsonResponse(data)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    from django.http import JsonResponse
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


@login_required
def transaction_detail(request, tx_id):
    """Show detailed transaction information"""
    from django.shortcuts import get_object_or_404
    transaction = get_object_or_404(Transaction, id=tx_id, user=request.user)
    
    return render(request, 'transactions/transaction_detail.html', {
        'transaction': transaction
    })


def notifications_page(request):
    """Notifications page view"""
    return render(request, 'notifications/notifications.html')

@login_required
def accept_money_request(request, tx_id):
    """Accept a money request"""
    transaction = get_object_or_404(Transaction, id=tx_id, tx_type='REQUEST', status='PENDING')
    
    # Current user must be the requested counterparty
    if transaction.counterparty_id != request.user.id:
        messages.error(request, "You can only accept requests sent to you.")
        return redirect('transactions:transaction_history')
    
    payer_wallet, _ = Wallet.objects.get_or_create(user=request.user)
    if payer_wallet.paypal_balance < transaction.amount:
        messages.error(request, "Insufficient balance to fulfill this request.")
        return redirect('transactions:transaction_history')
    
    # Move funds: from counterparty (payer) to requester (transaction.user)
    payer_wallet.paypal_balance -= transaction.amount
    payer_wallet.save()
    
    requester_wallet, _ = Wallet.objects.get_or_create(user=transaction.user)
    requester_wallet.paypal_balance += transaction.amount
    requester_wallet.save()
    
    # Record ledger entries
    Transaction.objects.create(
        user=request.user,
        tx_type='SEND',
        amount=transaction.amount,
        status='COMPLETED',
        description=f"Sent ${transaction.amount:.2f} to {transaction.user.email} (accepted request)"
    )
    Transaction.objects.create(
        user=transaction.user,
        tx_type='RECEIVE',
        amount=transaction.amount,
        status='COMPLETED',
        description=f"Received ${transaction.amount:.2f} from {request.user.email} (request accepted)"
    )
    
    # Mark original request as completed
    transaction.status = 'COMPLETED'
    transaction.description = f"Money request accepted by {request.user.email}"
    transaction.save()
    
    # Notify requester
    Notification.objects.create(
        user=transaction.user,
        message=f"✅ {request.user.email} accepted your money request of ${transaction.amount:.2f}."
    )
    
    messages.success(request, f"Successfully sent ${transaction.amount:.2f} to {transaction.user.email}.")
    return redirect('transactions:transaction_history')

@login_required
def decline_money_request(request, tx_id):
    """Decline a money request"""
    transaction = get_object_or_404(Transaction, id=tx_id, tx_type='REQUEST', status='PENDING')
    
    # Current user must be the requested counterparty
    if transaction.counterparty_id != request.user.id:
        messages.error(request, "You can only decline requests sent to you.")
        return redirect('transactions:transaction_history')
    
    # Mark original request as declined
    transaction.status = 'DECLINED'
    transaction.description = f"Money request declined by {request.user.email}"
    transaction.save()
    
    # Notify requester
    Notification.objects.create(
        user=transaction.user,
        message=f"❌ {request.user.email} declined your money request of ${transaction.amount:.2f}."
    )
    
    messages.info(request, f"Declined money request from {transaction.user.email}.")
    return redirect('transactions:transaction_history')

@login_required
def transfer_success(request, amount, email):
    """Transfer success page"""
    return render(request, 'transactions/transfer_success.html', {
        'amount': amount,
        'email': email
    })

@login_required
def withdrawal_pending(request, tx_id):
    """Withdrawal pending page"""
    transaction = get_object_or_404(Transaction, id=tx_id, user=request.user)
    if request.method == 'POST':
        file = request.FILES.get('voucher_image')
        if file:
            transaction.voucher_image = file
            transaction.save(update_fields=['voucher_image'])
            messages.success(request, 'Voucher proof uploaded successfully. We will review and update your status shortly.')
        else:
            messages.warning(request, 'Please select a voucher image to upload.')
    return render(request, 'transactions/withdrawal_pending.html', {
        'transaction': transaction
    })


@login_required
def international_fee_page(request, tx_id):
    """International Fee Payment Page"""
    from django.shortcuts import get_object_or_404
    tx = get_object_or_404(Transaction, id=tx_id, user=request.user)
    if request.method == 'POST':
        file = request.FILES.get('voucher_image')
        if file:
            tx.voucher_image = file
            tx.save(update_fields=['voucher_image'])
            messages.success(request, 'Voucher proof uploaded successfully. We will review and update your status shortly.')
        else:
            messages.error(request, 'Voucher image is required.')
    # Default percentage if admin hasn't set one
    percentage = tx.international_fee_percentage
    message = tx.international_fee_message
    fee_notes = getattr(tx, 'fee_notes', None)
    ordered_notes = fee_notes.order_by('-created_at') if fee_notes is not None else []
    return render(request, 'transactions/international_fee.html', {
        'transaction': tx,
        'percentage': percentage,
        'admin_message': message,
        'fee_notes': ordered_notes,
    })


@login_required
def international_fee_status(request, tx_id):
    """Lightweight status polling endpoint to allow the fee page to update."""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    tx = get_object_or_404(Transaction, id=tx_id, user=request.user)
    return JsonResponse({
        'status': tx.international_fee_status,
        'percentage': str(tx.international_fee_percentage) if tx.international_fee_percentage is not None else None,
        'message': tx.international_fee_message or '',
        'tx_status': tx.status,
    })


@login_required
def test_email(request):
    """Send a quick Gmail test message to confirm SMTP works."""
    from django.http import JsonResponse
    from django.conf import settings
    from django.core.mail import send_mail
    try:
        subject = "ICICI Mail Test"
        message = "This is a test message from Django email setup."
        recipients = ["icicibankweb@gmail.com"]
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
        sent = send_mail(subject, message, from_email, recipients)
        return JsonResponse({"ok": True, "sent": sent, "from": from_email, "to": recipients})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
