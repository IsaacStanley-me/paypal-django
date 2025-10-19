from django.urls import path
from . import views
app_name = 'accounts'  # ✅ this defines the namespace

urlpatterns = [
    path('', views.signup_step1, name='signup_step1'),
    path('signup/account-type/', views.signup_step1, name='signup_step1'),
    path('signup/email/', views.signup_email, name='signup_email'),
    path('signup/phone/', views.signup_phone, name='signup_phone'),
    path('signup/verification/', views.signup_verification, name='signup_verification'),
    path('signup/password/', views.signup_password, name='signup_password'),
    path('signup/personal-info/', views.signup_personal_info, name='signup_personal_info'),
    path('signup/address/', views.signup_address, name='signup_address'),
    path('signup/business-info/', views.signup_business_info, name='signup_business_info'),
    path('signup/profile-picture/', views.signup_profile_picture, name='signup_profile_picture'),
    path('signup/country/', views.signup_country, name='signup_country'),
    path('signup/details/', views.signup_details, name='signup_details'),
    path('phone-verification/', views.phone_verification_view, name='phone_verification'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/', views.settings_view, name='settings'),
    path('security/', views.security_view, name='security'),
    path('security/activity/', views.security_activity, name='security_activity'),
    path('security/change-password/', views.change_password, name='change_password'),
    path('security/verify-phone/', views.verify_phone_quick, name='verify_phone_quick'),
    path('contact-us/', views.contact_us_view, name='contact_us'),
    path('admin/contact-management/', views.admin_contact_management, name='admin_contact_management'),
    path('start-live-chat/', views.start_live_chat, name='start_live_chat'),
    path('admin/chat-management/', views.admin_chat_management, name='admin_chat_management'),
    path('chat/', views.chat_page, name='chat_page'),
    path('chat/send-message/', views.send_chat_message, name='send_chat_message'),
    path('chat/messages/<int:chat_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('chat/agent-join/<int:chat_id>/', views.agent_join_chat, name='agent_join_chat'),
]

