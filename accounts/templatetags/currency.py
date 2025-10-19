from decimal import Decimal, ROUND_HALF_UP
from django import template

register = template.Library()

# Simple demo rates relative to USD. In a real app fetch live rates.
CURRENCY_INFO = {
    'USD': {'symbol': '$',   'rate': Decimal('1.00')},
    'EUR': {'symbol': '€',   'rate': Decimal('0.92')},
    'GBP': {'symbol': '£',   'rate': Decimal('0.79')},
    'CAD': {'symbol': 'C$',  'rate': Decimal('1.36')},
    'AUD': {'symbol': 'A$',  'rate': Decimal('1.52')},
    'NZD': {'symbol': 'NZ$', 'rate': Decimal('1.69')},
    'JPY': {'symbol': '¥',   'rate': Decimal('156.0')},
    'CHF': {'symbol': 'CHF', 'rate': Decimal('0.90')},
    'CNY': {'symbol': '¥',   'rate': Decimal('7.25')},
    'INR': {'symbol': '₹',   'rate': Decimal('83.0')},
    'BRL': {'symbol': 'R$',  'rate': Decimal('5.6')},
    'MXN': {'symbol': 'MX$', 'rate': Decimal('19.0')},
    'KRW': {'symbol': '₩',   'rate': Decimal('1350')},
    'SGD': {'symbol': 'S$',  'rate': Decimal('1.35')},
    'HKD': {'symbol': 'HK$', 'rate': Decimal('7.80')},
    'ZAR': {'symbol': 'R',   'rate': Decimal('18.5')},
    'NGN': {'symbol': '₦',   'rate': Decimal('1600')},
    'GHS': {'symbol': '₵',   'rate': Decimal('15.2')},
}


def _format_amount(amount: Decimal) -> str:
    q = Decimal('0.01')
    return f"{amount.quantize(q, rounding=ROUND_HALF_UP):,.2f}"


@register.simple_tag(takes_context=True)
def money(context, amount):
    """Format a monetary amount according to the user's selected currency in session.
    Amounts are assumed to be stored in USD; convert using static rates for display only.
    Usage: {% money amount %}
    """
    try:
        amt = Decimal(str(amount or 0))
    except Exception:
        amt = Decimal('0')

    request = context.get('request')
    code = 'USD'
    if request is not None:
        code = request.session.get('currency', 'USD') or 'USD'
    info = CURRENCY_INFO.get(code, CURRENCY_INFO['USD'])

    converted = (amt * info['rate'])
    return f"{info['symbol']}{_format_amount(converted)}"


@register.simple_tag(takes_context=True)
def currency_symbol(context):
    request = context.get('request')
    code = 'USD'
    if request is not None:
        code = request.session.get('currency', 'USD') or 'USD'
    return CURRENCY_INFO.get(code, CURRENCY_INFO['USD'])['symbol']
