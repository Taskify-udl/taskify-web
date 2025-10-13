from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from taskify_app.models import Service, Contract

def home(request):
    return render(request, 'home.html')

def search(request):
    return render(request, 'search.html')

def login(request):
    return render(request, 'login.html')

def signup(request):
    return render(request, 'signup.html')

@login_required
def chats(request):
    return render(request, 'chats.html')

@login_required
def my_services(request):
    return render(request, 'my_services.html')

@login_required
def my_orders(request):
    return render(request, 'my_orders.html')

@login_required
def profile(request):
    user = request.user
    return render(request, 'profile.html', {'user': user})



