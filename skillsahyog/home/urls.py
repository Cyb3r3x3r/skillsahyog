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
    path("feedback",views.feedback,name="feedback"),
    path("check-username/", views.check_username_availability, name="check_username"),
    path("profile/settings/",views.account_settings,name="account_settings"),
]
