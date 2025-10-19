from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),
    path('card/<int:pk>/', views.card_detail, name='card_detail'),
    path('card/<int:pk>/delete/', views.delete_card, name='delete_card'),
    path('card/<int:pk>/upgrade/', views.upgrade_card, name='upgrade_card'),
    path('add-card/', views.add_card, name='add_card'),
    path('bank-accounts/', views.bank_accounts, name='bank_accounts'),
    path('add-bank-account/', views.add_bank_account, name='add_bank_account'),
    path('bank-account/<int:pk>/delete/', views.delete_bank_account, name='delete_bank_account'),
    path('bank-account/<int:pk>/verify/', views.verify_bank_account, name='verify_bank_account'),
]
