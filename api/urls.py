from django.urls import path
from . import views

urlpatterns = [
    path('register', views.auth_views.register),
    path('login', views.auth_views.login),
    path('profile', views.auth_views.profile),
]