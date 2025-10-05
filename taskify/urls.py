# taskify/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from taskify_app.api.viewsets import (
    CategoryViewSet,
    ServiceViewSet,
    ServiceCategoryViewSet,
    ContractViewSet,
    ReviewViewSet,
    FavoriteViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"service-categories", ServiceCategoryViewSet, basename="servicecategory")
router.register(r"contracts", ContractViewSet, basename="contract")
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"favorites", FavoriteViewSet, basename="favorite")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),            # ← aquí montas la API
    path("api-auth/", include("rest_framework.urls")),  # opcional
]
