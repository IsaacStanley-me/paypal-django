from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from transactions.models import Transaction
from wallet.models import Wallet

@staff_member_required
def approve_withdrawal(request, tx_id):
    tx = get_object_or_404(Transaction, id=tx_id, tx_type="WITHDRAW", status="PENDING")
    wallet = Wallet.objects.get(user=tx.user)
    if wallet.paypal_balance >= tx.amount:
        wallet.paypal_balance -= 0  # already deducted when request made
        wallet.save()
        tx.status = "COMPLETED"
        tx.save()
        messages.success(request, f"Withdrawal for {tx.user.email} approved!")
    else:
        messages.error(request, "Insufficient funds.")
    return redirect('/admin/transactions/transaction/')

@staff_member_required
def decline_withdrawal(request, tx_id):
    tx = get_object_or_404(Transaction, id=tx_id, tx_type="WITHDRAW", status="PENDING")
    wallet = Wallet.objects.get(user=tx.user)
    wallet.paypal_balance += tx.amount
    wallet.save()
    tx.status = "DECLINED"
    tx.save()
    messages.warning(request, f"Withdrawal for {tx.user.email} declined and refunded.")
    return redirect('/admin/transactions/transaction/')
