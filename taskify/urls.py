# taskify/urls.py
from django.contrib import admin
from django.template.context_processors import request
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from taskify_app import views

from rest_framework.authtoken import views as token_views

router = DefaultRouter()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    # Home
    path("", views.home, name='home'),

    # Header
    path("search/", views.search, name='search'),
    path("chats/", views.chats, name='chats'),
    path("my_services/", views.my_services, name='my_services'),
    path("my_orders/", views.my_orders, name='my_orders'),
    path("profile/", views.profile, name='profile'),
    path("profile/edit/", views.edit_profile, name='edit_profile'),
    path("profile/stats/", views.advanced_stats, name='advanced_stats'),
    path("notifications/", views.notifications, name='notifications'),
    path("notifications/mark-read/<int:notification_id>/", views.mark_notification_read, name='mark_notification_read'),

    path("login/", views.user_login , name='login'),
    path("signup/", views.signup, name='signup'),
]
