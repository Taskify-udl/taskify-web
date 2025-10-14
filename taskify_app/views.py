from urllib import response

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

from taskify_app.forms import RegisterForm
from taskify_app.models.user import CustomUser


def home(request):
    return render(request, 'home.html')

def search(request):
    return render(request, 'search.html')

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')


        user = CustomUser.objects.filter(username=username, is_active=True).first()
        if user is not None:
            authenticated_user = authenticate(username=username, password=password)
            if authenticated_user is not None:
                login(request, authenticated_user)
                return redirect("/home")

        error_message = "Usuario o contraseña incorrectos. Por favor, inténtalo de nuevo."
        return render(request, "registration/login.html", {"error_message": error_message})
    else:
        return render(request, "registration/login.html")

def signup(request):
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            form.save()
            username = response.POST.get('username')
            password = response.POST.get('password1')
            user = CustomUser.objects.filter(username=username, is_active=True).first()
            if user is not None:
                authenticated_user = authenticate(username=username, password=password)
                if authenticated_user is not None:
                    login(response, authenticated_user)
                    return redirect("/home")
            return redirect("/home")
    else:
        form = RegisterForm()

    return render(response, "registration/signup.html", {"form": form})

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



