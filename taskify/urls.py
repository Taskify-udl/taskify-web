# taskify/urls.py
from django.contrib import admin
from django.template.context_processors import request
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from taskify_app import views
from taskify_app.api.auth import RegisterView
from taskify_app.api.viewsets import (
    CategoryViewSet,
    ServiceViewSet,
    ServiceCategoryViewSet,
    ContractViewSet,
    ReviewViewSet,
    FavoriteViewSet,
)
from rest_framework.authtoken import views as token_views

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"service-categories", ServiceCategoryViewSet, basename="servicecategory")
router.register(r"contracts", ContractViewSet, basename="contract")
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"favorites", FavoriteViewSet, basename="favorite")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/login", token_views.obtain_auth_token),
    path("api-auth/", include("rest_framework.urls")),

    path("api-auth/register/", RegisterView.as_view(), name="register"),

    # Home
    path("", views.home, name='home'),

    # Header
    path("search/", views.search, name='search'),
    path("chats/", views.chats, name='chats'),
    path("my_services/", views.my_services, name='my_services'),
    path("my_orders/", views.my_orders, name='my_orders'),
    path("profile/", views.profile, name='profile'),

    path("login/", views.login, name='login'),
    path("signup/", views.signup, name='signup'),
]
