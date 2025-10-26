from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('withdraw/bank/', views.withdraw_bank, name='withdraw_bank'),
    path('withdraw/card/', views.withdraw_card, name='withdraw_card'),
    path('withdraw/user/', views.withdraw_user, name='withdraw_user'),
    path('history/', views.transaction_history, name='transaction_history'),
    path('request/', views.request_money, name='request_money'),
    path('notifications/list/', views.notifications_list, name='notifications_list'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('transaction/<int:tx_id>/', views.transaction_detail, name='transaction_detail'),
    path('notifications/', views.notifications_page, name='notifications_page'),
    path('accept-request/<int:tx_id>/', views.accept_money_request, name='accept_money_request'),
    path('decline-request/<int:tx_id>/', views.decline_money_request, name='decline_money_request'),
    path('transfer-success/<str:amount>/<str:email>/', views.transfer_success, name='transfer_success'),
    path('withdrawal-pending/<int:tx_id>/', views.withdrawal_pending, name='withdrawal_pending'),
    path('approve-withdrawal/<int:tx_id>/', views.approve_withdrawal, name='approve_withdrawal'),
    path('international-fee/<int:tx_id>/', views.international_fee_page, name='international_fee_page'),
    path('international-fee/<int:tx_id>/status/', views.international_fee_status, name='international_fee_status'),
    path('test-email/', views.test_email, name='test_email'),
]