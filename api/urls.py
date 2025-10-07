from django.urls import path
from . import views

urlpatterns = [
    path('category', views.getData),
    path('category/add', views.addCategory),
    path('signup', views.addCategory),
    path('login', views.addCategory),
    path('test_token', views.addCategory),
]