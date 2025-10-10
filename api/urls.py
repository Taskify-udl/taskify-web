from django.urls import path
from .views import review_views, contract_views, category_views, service_views, favorite_views, auth_views

urlpatterns = [
    path('register', auth_views.register),
    path('login', auth_views.login),
    path('profile', auth_views.profile),
    path('service', service_views.services),
    path('service/<int:pk>', service_views.service_detail),
    path('review', review_views.reviews),
    path('review/<int:pk>', review_views.review_detail),
    path('contract', contract_views.contracts),
    path('contract/<int:pk>', contract_views.contract_detail),
    path('category', category_views.categories),
    path('category/<int:pk>', category_views.category_detail),
    path('favorite', favorite_views.favorites),  # GET y POST
    path('favorite/<int:pk>', favorite_views.favorite_detail),  # DELETE

]