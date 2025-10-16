from urllib import response
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta



from .forms import RegisterForm
from .models import Service, Contract, Review, UserProfile, Notification, CustomUser, EmailVerification

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
                return redirect("home")
        error_message = "Usuario o contraseña incorrectos. Por favor, inténtalo de nuevo."
        return render(request, "registration/login.html", {"error_message": error_message})
    return render(request, "registration/login.html")


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Ya existe un usuario con ese correo.")
            return redirect('signup')

        user = CustomUser.objects.create_user(username=username, email=email, password=password)
        user.is_active = False
        user.save()

        verification, _ = EmailVerification.objects.get_or_create(user=user)
        verification.generate_code()

        # Enviar correo
        send_mail(
            subject="Verifica tu cuenta en Taskify",
            message=f"Tu código de verificación es: {verification.code}",
            from_email="no-reply@taskify.com",
            recipient_list=[email],
        )

        request.session['pending_email'] = email

        return redirect('verify_email')

    return render(request, 'registration/signup.html')


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

    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Get user's services with pagination
    services_list = Service.objects.filter(provider=user).order_by('-created_at')
    services_paginator = Paginator(services_list, 5)  # 5 services per page
    services_page = request.GET.get('services_page')
    user_services = services_paginator.get_page(services_page)

    # Get user's contracts with pagination
    contracts_list = Contract.objects.filter(user=user).order_by('-created_at')
    contracts_paginator = Paginator(contracts_list, 5)  # 5 contracts per page
    contracts_page = request.GET.get('contracts_page')
    user_contracts = contracts_paginator.get_page(contracts_page)

    # Get reviews received for user's services
    user_reviews = Review.objects.filter(service__provider=user).order_by('-created_at')

    # Calculate statistics
    services_count = services_list.count()
    contracts_count = contracts_list.count()
    reviews_count = user_reviews.count()
    average_rating = user_reviews.aggregate(models.Avg('rating'))['rating__avg'] if user_reviews.exists() else 0

    # Get unread notifications count
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()

    context = {
        'user': user,
        'profile': profile,
        'user_services': user_services,
        'user_contracts': user_contracts,
        'user_reviews': user_reviews[:3],  # Show only latest 3 reviews
        'services_count': services_count,
        'contracts_count': contracts_count,
        'reviews_count': reviews_count,
        'average_rating': average_rating,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Update user basic info
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()

        # Update profile info
        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')
        profile.location = request.POST.get('location', '')
        profile.website = request.POST.get('website', '')

        # Handle avatar upload
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']

        profile.save()

        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('profile')

    return render(request, 'edit_profile.html', {'profile': profile})


@login_required
def advanced_stats(request):
    user = request.user

    # Basic statistics
    services_count = Service.objects.filter(provider=user).count()
    contracts_count = Contract.objects.filter(user=user).count()
    reviews_count = Review.objects.filter(service__provider=user).count()

    # Monthly statistics (last 12 months)
    from django.db.models.functions import TruncMonth
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta

    # Services created by month
    services_by_month = Service.objects.filter(
        provider=user,
        created_at__gte=timezone.now() - relativedelta(months=12)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    # Contracts by month
    contracts_by_month = Contract.objects.filter(
        user=user,
        created_at__gte=timezone.now() - relativedelta(months=12)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    # Reviews by month
    reviews_by_month = Review.objects.filter(
        service__provider=user,
        created_at__gte=timezone.now() - relativedelta(months=12)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    # Rating distribution
    rating_distribution = Review.objects.filter(
        service__provider=user
    ).values('rating').annotate(
        count=Count('rating')
    ).order_by('rating')

    # Top performing services
    top_services = Service.objects.filter(provider=user).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).filter(review_count__gt=0).order_by('-avg_rating')[:5]

    # Recent activity
    recent_contracts = Contract.objects.filter(user=user).order_by('-created_at')[:10]
    recent_reviews = Review.objects.filter(service__provider=user).order_by('-created_at')[:10]

    context = {
        'services_count': services_count,
        'contracts_count': contracts_count,
        'reviews_count': reviews_count,
        'services_by_month': list(services_by_month),
        'contracts_by_month': list(contracts_by_month),
        'reviews_by_month': list(reviews_by_month),
        'rating_distribution': list(rating_distribution),
        'top_services': top_services,
        'recent_contracts': recent_contracts,
        'recent_reviews': recent_reviews,
    }

    return render(request, 'advanced_stats.html', context)


@login_required
def notifications(request):
    notifications_list = Notification.objects.filter(user=request.user)
    unread_count = notifications_list.filter(is_read=False).count()

    # Mark all as read if requested
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        notifications_list.update(is_read=True)
        messages.success(request, 'Todas las notificaciones han sido marcadas como leídas.')
        return redirect('notifications')

    # Pagination
    paginator = Paginator(notifications_list, 10)  # 10 notifications per page
    page = request.GET.get('page')
    notifications = paginator.get_page(page)

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notificación no encontrada'})


@login_required
def create_notification(user, title, message, notification_type='system', **kwargs):
    """Helper function to create notifications"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        **kwargs
    )
    return notification


def verify_email(request):
    email = request.session.get('pending_email')
    if not email:
        messages.error(request, 'Sesión expirada. Por favor, regístrate nuevamente.')
        return redirect('signup')

    error_message = None

    if request.method == 'POST':
        code = request.POST.get('verification_code', '').strip()
        try:
            user = CustomUser.objects.get(email=email)
            verification = EmailVerification.objects.get(user=user)
        except (CustomUser.DoesNotExist, EmailVerification.DoesNotExist):
            error_message = "Error interno, inténtalo más tarde."
        else:
            if verification.code == code and verification.created_at > timezone.now() - timedelta(minutes=10):
                user.is_active = True
                user.save()
                verification.delete()
                del request.session['pending_email']

                login(request, user)
                messages.success(request, '¡Cuenta verificada exitosamente! Bienvenido.')
                return redirect('home')
            else:
                error_message = "Código incorrecto o expirado."

    return render(request, 'verify_email.html', {'email': email, 'error_message': error_message})


@csrf_exempt
def resend_verification_code(request):
    email = request.session.get('pending_email')
    if not email:
        return JsonResponse({'success': False, 'error': 'Sesión expirada.'})

    try:
        user = CustomUser.objects.get(email=email)
        verification, _ = EmailVerification.objects.get_or_create(user=user)
        verification.generate_code()

        send_mail(
            subject="Tu código de verificación",
            message=f"Tu código de verificación es: {verification.code}",
            from_email="no-reply@taskify.com",
            recipient_list=[email],
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

