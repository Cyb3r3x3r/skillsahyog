# home/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('features',views.features,name="features"),
    path('howitworks',views.howitworks,name="howitworks"),
    path('signup',views.signup,name="signup"),
    path('signin',views.signin,name="signin"),
    path('dashboard',views.dashboard,name="dashboard"),
    path('user_logout',views.user_logout,name="user_logout"),
    path('user_profile/<str:username>/', views.user_profile, name='user_profile'),
    path('exchange/send/<str:receiver_id>/', views.send_exchange_request, name='send_exchange_request'),
    path('exchange/accept/<int:request_id>/', views.accept_exchange_request, name='accept_exchange_request'),
    path('exchange/reject/<int:request_id>/', views.reject_exchange_request, name='reject_exchange_request'),
    path("forgot-password/", views.forgot_password_request, name="forgot_password_request"),
    path("forgot-password/verify/", views.forgot_password_verify, name="forgot_password_verify"),
    path("forgot-password/reset/", views.forgot_password_reset, name="forgot_password_reset"),
    path("chat/<str:chat_id>/", views.chat_page, name="chat_page"),
    path("api/chat_rooms/", views.get_chat_rooms, name="api_chat_rooms"),
    path("api/messages/<str:chat_id>/", views.get_messages, name="api_get_messages"),
    path("api/send_message/", views.send_message, name="api_send_message"),
    path("manage-skills",views.manage_skills,name="manage_skills"),
    path("feedback/<int:exchange_id>/",views.feedback,name="feedback"),
    path("check-username/", views.check_username_availability, name="check_username"),
    path("profile/settings/",views.profile_settings,name="profile_settings"),
    path("profile/notifications/",views.notification,name="notifications"),
    path("calculate-skill-score/<int:exchange_id>/", views.calculate_skill_score, name="calculate_skill_score"),
    path('my-feedbacks/', views.view_feedbacks, name='my_feedbacks'),
    path('my_exchanges/', views.view_exchanges, name='my_exchanges'),
    path('account-settings/', views.account_settings, name='account_settings'),
    path('disable-account/', views.disable_account, name='disable_account'),
    path('match-skill/', views.match_skill, name='match_skill'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_and_conditions, name='terms'),
    path('submit-contact/', views.submit_contact_form, name='submit_contact_form'),
    path('contact/mark-read/<int:message_id>/', views.mark_contact_message_read, name='mark_contact_message_read'),
    path('mod/manage-users/', views.manage_users, name='manage_users'),
    path('mod/toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('about',views.about,name="about")
]
