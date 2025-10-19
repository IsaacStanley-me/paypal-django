from django.urls import path
from . import views

app_name = 'rewards'

urlpatterns = [
    path('', views.rewards_dashboard, name='dashboard'),
    path('mark-paid/', views.mark_activation_paid, name='mark_paid'),
    path('convert/', views.convert_points, name='convert'),
    path('claim/', views.claim_activity, name='claim'),
    path('pending/<int:tx_id>/', views.pending_conversion, name='pending'),
]
