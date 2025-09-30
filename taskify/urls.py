from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()


urlpatterns = [
    path("admin/", admin.site.urls),

    # API DRF
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),  # login/logout del browsable API

]
