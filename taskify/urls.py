# taskify/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from taskify_app import views

urlpatterns = [
    path("set-language/", views.set_language, name="set_language"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api/validate-signup/", views.validate_signup, name='validate_signup'),
    path('accounts/', include('allauth.urls')),
    path('api/save-signup-session/', views.save_signup_data_session, name='save_signup_session'),

    path("", views.home, name='home'),

    path("login/", views.user_login, name='login'),
    path("signup/", views.signup, name='signup'),
    path("logout/", views.user_logout, name="logout"),

    path("search/", views.search, name='search'),

    path('chats/', views.chat_list_view, name='chats'),
    path('chat/<int:conversation_id>/', views.chat_detail_view, name='chat_detail'),

    path("my_services/", views.my_services, name='my_services'),
    path('my_services/delete/<int:service_id>/', views.delete_service, name='delete_service'),

    path("service/<int:service_id>/", views.service_detail, name="service_detail"),
    path("service/<int:service_id>/contact/", views.start_chat, name="start_chat"),
    path("service/<int:service_id>/request/", views.request_service, name="request_service"),

    path("my_orders/", views.my_orders, name='my_orders'),
    path("order/<int:contract_id>/cancel/", views.cancel_contract, name='cancel_contract'),
    path("agenda/", views.provider_agenda, name='provider_agenda'),
    path("order/<int:contract_id>/chat/", views.start_chat_order, name='start_chat_order'),
    path("favourites/", views.favourites, name='favourites'),
    path("service/<int:service_id>/toggle-favorite/", views.toggle_favorite, name='toggle_favorite'),

    path("profile/", views.profile, name='profile'),
    path("user/<str:username>/", views.public_profile, name="public_profile"),
    path("profile/edit/", views.edit_profile, name='edit_profile'),
    path("profile/stats/", views.advanced_stats, name='advanced_stats'),

    path("notifications/", views.notifications, name='notifications'),
    path("notifications/mark-read/<int:notification_id>/", views.mark_notification_read, name='mark_notification_read'),

    path("verify-email/", views.verify_email, name="verify_email"),
    path("resend-verification-code/", views.resend_verification_code, name="resend_verification_code"),
    path("order/<int:contract_id>/qr/<str:type>/", views.contract_qr_code, name="contract_qr_code"),
    path('order/<int:contract_id>/verify/', views.verify_service_code, name='verify_service_code'),
    # URLs públicas para iniciar/terminar servicio vía token incluidos en QR
    path('order/<int:contract_id>/toggle-pause/', views.toggle_pause_service, name='toggle_pause_service'),
    path('promote-service/', views.promote_service, name='promote_service'),
]

# Servir MEDIA en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
