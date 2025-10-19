from django.urls import path
from . import views

urlpatterns = [
    path('withdraw/approve/<int:tx_id>/', views.approve_withdrawal, name='approve_withdrawal'),
    path('withdraw/decline/<int:tx_id>/', views.decline_withdrawal, name='decline_withdrawal'),
]
