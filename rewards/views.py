from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from wallet.models import Wallet
from .models import RewardAccount, RewardTransaction, RewardConversionSettings, RewardActivityType, RewardActivityLog
from django.utils.timezone import now
from datetime import timedelta


def _get_or_create_reward_account(user):
    acc, _ = RewardAccount.objects.get_or_create(user=user)
    return acc

def _ensure_default_activities():
    """Create a rich set (>15) of default activities if they don't exist"""
    defaults = [
        # code, name, points, frequency, claimable
        ("REFERRAL_BONUS", "Referral Bonus", 200, "UNLIMITED", False),
        ("DAILY_LOGIN", "Daily Login", 10, "DAILY", True),
        ("VERIFY_EMAIL", "Verify Email", 50, "ONCE", True),
        ("COMPLETE_PROFILE", "Complete Profile", 40, "ONCE", True),
        ("ADD_PROFILE_PHOTO", "Add Profile Photo", 20, "ONCE", True),
        ("ENABLE_2FA", "Enable Two-Factor Auth", 60, "ONCE", True),
        ("ADD_CARD", "Link a Card", 30, "ONCE", True),
        ("ADD_BANK", "Link a Bank Account", 30, "ONCE", True),
        ("FIRST_DEPOSIT", "Make First Deposit", 80, "ONCE", False),
        ("FIRST_TRANSACTION", "Complete First Transaction", 80, "ONCE", False),
        ("SEND_MONEY", "Send Money", 10, "DAILY", False),
        ("RECEIVE_MONEY", "Receive Money", 10, "DAILY", False),
        ("REQUEST_MONEY", "Request Money", 10, "DAILY", False),
        ("INVITE_FRIEND", "Invite a Friend", 100, "UNLIMITED", False),
        ("WATCH_TUTORIAL", "Watch Tutorial", 15, "ONCE", True),
        ("LEAVE_FEEDBACK", "Share Feedback", 15, "UNLIMITED", True),
        ("MILESTONE_1000PTS", "Reach 1000 Points", 50, "ONCE", False),
        ("LINK_APP", "Install Mobile App", 50, "ONCE", True),
    ]
    for code, name, pts, freq, claimable in defaults:
        RewardActivityType.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'points': pts,
                'frequency': freq,
                'claimable': claimable,
                'active': True,
            }
        )

@login_required
def rewards_dashboard(request):
    user = request.user
    _ensure_default_activities()
    settings = RewardConversionSettings.objects.first()
    account = _get_or_create_reward_account(user)
    history = RewardTransaction.objects.filter(user=user).order_by('-created_at')
    # Prepare activities list with claim status
    activities = RewardActivityType.objects.filter(active=True).order_by('name')
    activity_states = []
    today = now().date()
    for a in activities:
        can_claim = False
        reason = ''
        if not a.claimable:
            can_claim = False
            reason = 'Awarded automatically'
        else:
            if a.frequency == 'ONCE':
                already = RewardActivityLog.objects.filter(user=user, activity=a).exists()
                can_claim = not already
                reason = 'Already claimed' if already else ''
            elif a.frequency == 'DAILY':
                already_today = RewardActivityLog.objects.filter(user=user, activity=a, created_at__date=today).exists()
                can_claim = not already_today
                reason = 'Already claimed today' if already_today else ''
            else:
                can_claim = True
        activity_states.append({
            'obj': a,
            'can_claim': can_claim,
            'reason': reason,
        })
    return render(request, 'rewards/rewards_dashboard.html', {
        'settings': settings,
        'account': account,
        'history': history,
        'activities': activity_states,
    })


@login_required
def mark_activation_paid(request):
    if request.method != 'POST':
        return redirect('rewards:dashboard')


@login_required
def pending_conversion(request, tx_id: int):
    user = request.user
    try:
        tx = RewardTransaction.objects.get(id=tx_id, user=user, tx_type='CONVERT')
    except RewardTransaction.DoesNotExist:
        messages.error(request, 'Pending conversion not found.')
        return redirect('rewards:dashboard')
    settings = RewardConversionSettings.objects.first()
    return render(request, 'rewards/pending_conversion.html', {
        'tx': tx,
        'settings': settings,
    })

    account.activation_paid = True
    account.activation_paid_at = timezone.now()
    account.save()

    RewardTransaction.objects.create(
        user=request.user,
        tx_type='ACTIVATION',
        points=0,
        amount=settings.activation_fee,
        description=f'Activation fee marked paid to {settings.pay_to_email}'
    )
    messages.success(request, 'Activation marked as paid. You can now convert your points to cash.')
    return redirect('rewards:dashboard')


@login_required
def convert_points(request):
    if request.method != 'POST':
        return redirect('rewards:dashboard')
    settings = RewardConversionSettings.objects.first()
    if not settings:
        messages.error(request, 'Conversion settings not configured yet. Contact admin.')
        return redirect('rewards:dashboard')

    account = _get_or_create_reward_account(request.user)

    try:
        # Convert either all points or specified value
        points_to_convert = int(request.POST.get('points', account.points))
    except ValueError:
        messages.error(request, 'Invalid points value.')
        return redirect('rewards:dashboard')

    ppb = int(settings.points_per_block or 100)
    if points_to_convert < ppb:
        messages.error(request, f'Minimum conversion is {ppb} points.')
        return redirect('rewards:dashboard')

    if points_to_convert % ppb != 0:
        messages.error(request, f'Points must be in multiples of {ppb}.')
        return redirect('rewards:dashboard')

    if points_to_convert > account.points:
        messages.error(request, 'You cannot convert more points than you have.')
        return redirect('rewards:dashboard')

    blocks = points_to_convert // ppb
    payout_per_block = float(settings.payout_per_block or 0)
    fee_per_block = float(settings.fee_per_block or 0)
    amount = blocks * payout_per_block
    total_fee = blocks * fee_per_block

    # Require user confirmation that fee has been paid for this conversion
    if request.POST.get('confirm_fee') != 'on':
        messages.error(request, f'Please confirm the conversion fee payment (${total_fee:.2f}).')
        return redirect('rewards:dashboard')

    # Collect payout account and optional receipt reference
    payout_account = request.POST.get('payout_account', '').strip()
    receipt_reference = request.POST.get('receipt_reference', '').strip()
    receipt_image = request.FILES.get('receipt_image')

    # Create a PENDING conversion transaction; admin will approve to finalize
    tx = RewardTransaction.objects.create(
        user=request.user,
        tx_type='CONVERT',
        status='PENDING',
        points=points_to_convert,
        amount=amount,
        blocks=blocks,
        fee_amount=total_fee,
        payout_account=payout_account,
        receipt_reference=receipt_reference,
        receipt_image=receipt_image,
        description=f'Requested conversion: {points_to_convert} points ({blocks} blocks) to ${amount:.2f}; fee ${total_fee:.2f}'
    )

    messages.success(request, f'Conversion request submitted: {points_to_convert} points → ${amount:.2f}. Fee ${total_fee:.2f}. Awaiting ICICI Bank Approval.')
    return redirect('rewards:pending', tx_id=tx.id)


@login_required
def claim_activity(request):
    if request.method != 'POST':
        return redirect('rewards:dashboard')
    code = request.POST.get('code')
    try:
        activity = RewardActivityType.objects.get(code=code, active=True)
    except RewardActivityType.DoesNotExist:
        messages.error(request, 'Invalid activity.')
        return redirect('rewards:dashboard')

    if not activity.claimable:
        messages.error(request, 'This activity cannot be claimed manually.')
        return redirect('rewards:dashboard')

    user = request.user
    account = _get_or_create_reward_account(user)
    today = now().date()
    if activity.frequency == 'ONCE' and RewardActivityLog.objects.filter(user=user, activity=activity).exists():
        messages.info(request, 'You already claimed this activity.')
        return redirect('rewards:dashboard')
    if activity.frequency == 'DAILY' and RewardActivityLog.objects.filter(user=user, activity=activity, created_at__date=today).exists():
        messages.info(request, 'You already claimed this activity today.')
        return redirect('rewards:dashboard')

    # Award points
    account.points += activity.points
    account.save()
    RewardActivityLog.objects.create(user=user, activity=activity, points=activity.points)
    RewardTransaction.objects.create(user=user, tx_type='EARN', points=activity.points, amount=0, description=f'Earned via {activity.name}')
    messages.success(request, f'+{activity.points} points earned from {activity.name}.')
    return redirect('rewards:dashboard')

# Create your views here.
from django.shortcuts import render

def rewards_view(request):
    user = request.user
    reward_points = 150  # Example — later we can fetch this from a model
    return render(request, "rewards/rewards.html", {"reward_points": reward_points})
