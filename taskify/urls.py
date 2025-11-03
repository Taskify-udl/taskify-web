# taskify/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from taskify_app import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),

    path("", views.home, name='home'),

    path("login/", views.user_login, name='login'),
    path("signup/", views.signup, name='signup'),
    path("logout/", views.user_logout, name="logout"),

    path("search/", views.search, name='search'),
    path("chats/", views.chats, name='chats'),

    path('my_services/', views.my_services, name='my_services'),
    path('my_services/delete/<int:service_id>/', views.delete_service, name='delete_service'),

    path("my_orders/", views.my_orders, name='my_orders'),
    path("profile/", views.profile, name='profile'),

    path("profile/edit/", views.edit_profile, name='edit_profile'),
    path("profile/stats/", views.advanced_stats, name='advanced_stats'),
    path("notifications/", views.notifications, name='notifications'),
    path("notifications/mark-read/<int:notification_id>/", views.mark_notification_read, name='mark_notification_read'),

    path("verify-email/", views.verify_email, name="verify_email"),
    path("resend-verification-code/", views.resend_verification_code, name="resend_verification_code"),
]

# Servir MEDIA en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
