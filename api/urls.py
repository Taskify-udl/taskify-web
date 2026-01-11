from django.urls import path
from .views import review_views, contract_views, category_views, service_views, favorite_views, auth_views, user_views, email_verification_views, conversation_views
from taskify_app import views

urlpatterns = [
    path('register', auth_views.register),
    path('login', auth_views.login),
    path('profile', auth_views.profile),
    path('profile/<int:pk>', user_views.public_profile_detail),
    path('profile_detail', user_views.profile_detail),
    path('service', service_views.services),
    path('service/<int:pk>', service_views.service_detail),
    path('review', review_views.reviews),
    path('review/<int:pk>', review_views.review_detail),
    path('contract', contract_views.contracts),
    path('contract/mine', contract_views.my_contracts),
    path('contract/<int:pk>', contract_views.contract_detail),
    path('contract/<int:contract_id>/start', contract_views.contract_start),
    path('contract/<int:contract_id>/stop', contract_views.contract_stop),
    path('category', category_views.categories),
    path('category/<int:pk>', category_views.category_detail),
    path('favorite', favorite_views.favorites), 
    path('favorite/<int:pk>', favorite_views.favorite_detail),  
    path('chat/<int:conversation_id>/new-messages/', views.get_new_messages, name='get_new_messages'),
    path('change-password', user_views.change_password),
    path('verification-code', email_verification_views.get_verification_code),
    path('contract/<int:contract_id>/review/', views.create_review, name='create_review'),

    # Chat / Conversations API
    path('conversation', conversation_views.conversations),
    path('conversation/<int:pk>', conversation_views.conversation_detail),
    path('conversation/<int:pk>/messages', conversation_views.conversation_messages),
    path('conversation/<int:pk>/mark-read', conversation_views.conversation_mark_read),
]
