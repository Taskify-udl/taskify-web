from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import logout
from django.urls import reverse
import json
import random

from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from core.decorators import allowed_roles
from .forms import RegisterForm
from django.templatetags.static import static
from .models import Service, ServiceImage, Contract, Review, Notification, CustomUser, EmailVerification, \
    Category, Conversation, Message, Favorite


@ensure_csrf_cookie
@ensure_csrf_cookie
def home(request):
    # Seleccionar hasta 6 categorías aleatorias
    all_categories = list(Category.objects.all())
    if len(all_categories) > 6:
        categories = random.sample(all_categories, 6)
    else:
        categories = all_categories

    # Servicios destacados paginados (ordenados por rating o fecha)
    featured_services_list = Service.objects.annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-avg_rating', '-created_at')
    
    paginator = Paginator(featured_services_list, 12)
    page_number = request.GET.get('page')
    featured_services = paginator.get_page(page_number)

    user_favorites = {}
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user).values('id', 'service_id')
        user_favorites = {fav['service_id']: fav['id'] for fav in favorites}

    context = {
        'categories': categories,
        'featured_services': featured_services,
        'page_obj': featured_services, # Para el template de paginación
        'user_favorites_json': json.dumps(user_favorites),
    }
    return render(request, 'home.html', context)




@require_POST
def set_language(request):
    lang = request.POST.get("language", "es")
    # Limitamos a los idiomas que realmente tenemos
    if lang not in ("es", "en", "ca"):
        lang = "es"

    request.session["lang"] = lang

    # Volver a la página anterior o a la home
    next_url = request.POST.get("next") or "/"
    return redirect(next_url)


from django.db.models import Q, Avg, Count
import json

def search(request):
    """
    Vista para la página de resultados de búsqueda.
    Filtra por término de búsqueda (q) o por categoría.
    """
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')  # e.g. "46"

    # Empezamos con todos los servicios y optimizamos la consulta
    results = Service.objects.all().select_related(
        'provider__profile'
    ).prefetch_related(
        'images', 'categories', 'reviews'
    )

    # 1. Filtrar por término de búsqueda (en nombre o descripción)
    if query:
        results = results.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    # 2. Filtrar por categoría (ManyToMany)
    if category_id:
        results = results.filter(categories__id=category_id)

    # Añadimos anotaciones para la media de estrellas (para mostrar en las tarjetas)
    results = results.annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).distinct()

    # Paginación
    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # (Pasamos los favoritos del usuario para los botones de corazón)
    user_favorites = {}
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user).values('id', 'service_id')
        user_favorites = {fav['service_id']: fav['id'] for fav in favorites}

    context = {
        'query': query,
        'category_id': category_id,  # por si quieres marcar la categoría activa en la plantilla
        'results': page_obj,
        'page_obj': page_obj,
        'user_favorites_json': json.dumps(user_favorites),
    }

    return render(request, 'search.html', context)



@login_required
def favourites(request):
    """
    Pantalla de servicios favoritos del usuario autenticado.
    """
    from .models import Favorite

    user = request.user
    favorite_services_list = Service.objects.filter(
        favorited_by__user=user
    ).prefetch_related('categories', 'images').order_by('-favorited_by__favorited_at')

    paginator = Paginator(favorite_services_list, 12)
    page_number = request.GET.get('page')
    favorite_services = paginator.get_page(page_number)

    context = {
        'favorite_services': favorite_services,
        'page_obj': favorite_services,
    }
    return render(request, 'favourites.html', context)


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

        if CustomUser.objects.filter(username__iexact=username, is_active=True).exists():
            messages.error(request, f"El nombre de usuario '{username}' ya está en uso. Por favor, elige otro.")
            return redirect('signup')

        if CustomUser.objects.filter(email__iexact=email, is_active=True).exists():
            messages.error(request, f"El correo electrónico '{email}' ya está registrado. Por favor, inicia sesión.")
            return redirect('signup')

        user = CustomUser.objects.filter(email__iexact=email, is_active=False).first()

        if user:
            if CustomUser.objects.filter(username__iexact=username).exclude(email__iexact=email).exists():
                messages.error(request, f"El nombre de usuario '{username}' ya está en uso. Por favor, elige otro.")
                return redirect('signup')

            user.username = username
            user.set_password(password)
            user.save()

        else:
            user = CustomUser.objects.filter(username__iexact=username, is_active=False).first()
            if user:
                user.email = email
                user.set_password(password)
                user.save()
            else:
                user = CustomUser.objects.create_user(username=username, email=email, password=password)
                user.is_active = False
                user.save()

        verification, _ = EmailVerification.objects.get_or_create(user=user)
        verification.generate_code()

        send_mail(
            subject="Verifica tu cuenta en Taskify",
            message=f"Tu código de verificación es: {verification.code}",
            from_email="no-reply@taskify.com",
            recipient_list=[email],
        )

        request.session['pending_email'] = email
        return redirect('verify_email')

    return render(request, 'registration/signup.html')


def validate_signup(request):
    """
    Una vista API para validar username y email en tiempo real
    desde el formulario de registro.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()

            username_taken = CustomUser.objects.filter(username__iexact=username, is_active=True).exists()
            email_taken = CustomUser.objects.filter(email__iexact=email, is_active=True).exists()

            return JsonResponse({
                'username_taken': username_taken,
                'email_taken': email_taken,
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def user_logout(request):
    # Recomendado: cerrar sesión solo por POST para evitar CSRF por enlaces GET
    if request.method != 'POST':
        return redirect("home")
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect("login")


@login_required
def my_orders(request):
    user = request.user

    if request.method == 'POST' and user.is_provider:
        contract_id = request.POST.get('contract_id')
        action = request.POST.get('action')
        next_status = {
            'accept': 'accepted',
            'reject': 'rejected',
        }.get(action)

        if contract_id and next_status:
            try:
                contract = get_object_or_404(
                    Contract, pk=contract_id
                )
                
                # Validación de permisos usando el método del modelo
                if not contract.can_be_accepted_by(user):
                    messages.error(request, 'No tienes permiso para modificar este contrato.')
                    return redirect('my_orders')
                
                if contract.status != next_status:
                    contract.status = next_status
                    if next_status == 'rejected':
                        contract.rejection_reason = request.POST.get('rejection_reason', '')
                        contract.save(update_fields=['status', 'rejection_reason'])
                        
                        # Crear notificación de rechazo
                        create_notification(
                            user=contract.user,
                            title="Solicitud rechazada",
                            message=f"Tu solicitud para '{contract.service.name}' ha sido rechazada. Motivo: {contract.rejection_reason}",
                            notification_type='contract_rejected',
                            contract=contract
                        )
                        messages.info(request, 'Has rechazado la solicitud. El cliente será notificado.')
                    else:
                        contract.save(update_fields=['status'])
                        
                        # Crear notificación de aceptación
                        create_notification(
                            user=contract.user,
                            title="¡Solicitud aceptada!",
                            message=f"Tu solicitud para '{contract.service.name}' ha sido   aceptada para el {contract.start_date.strftime('%d/%m/%Y')} a las {contract.start_time.strftime('%H:%M')}.",
                            notification_type='contract_accepted',
                            contract=contract
                        )
                        messages.success(request, 'Has aceptado la solicitud. El cliente será notificado.')
                        
            except Exception as e:
                messages.error(request, f'Error al procesar la solicitud: {str(e)}')
                
        return redirect('my_orders')

    if user.is_provider:
        contracts_qs = (
            Contract.objects.filter(service__provider=user)
            .select_related('service', 'user')
            .order_by('-created_at')
        )
    else:
        contracts_qs = (
            Contract.objects.filter(user=user)
            .select_related('service', 'service__provider')
            .order_by('-created_at')
        )

    status_styles = {
        'pending': {
            'badge_classes': 'bg-amber-100 text-amber-700',
            'dot_classes': 'bg-amber-500',
            'label': 'Pendiente de aceptar',
            'group': 'pending',
        },
        'accepted': {
            'badge_classes': 'bg-green-100 text-green-700',
            'dot_classes': 'bg-green-500',
            'label': 'Aceptado',
            'group': 'accepted',
        },
        'rejected': {
            'badge_classes': 'bg-red-100 text-red-700',
            'dot_classes': 'bg-red-500',
            'label': 'Rechazado',
            'group': 'rejected',
        },
        'active': {
            'badge_classes': 'bg-blue-100 text-blue-700',
            'dot_classes': 'bg-blue-500',
            'label': 'Aceptado',
            'group': 'accepted',
        },
        'finished': {
            'badge_classes': 'bg-green-100 text-green-700',
            'dot_classes': 'bg-green-500',
            'label': 'Completado',
            'group': 'accepted',
        },
        'cancelled': {
            'badge_classes': 'bg-red-100 text-red-700',
            'dot_classes': 'bg-red-500',
            'label': 'Cancelado',
            'group': 'rejected',
        },
        'paused': {
            'badge_classes': 'bg-gray-100 text-gray-700',
            'dot_classes': 'bg-gray-400',
            'label': 'En pausa',
            'group': 'pending',
        },
    }

    status_totals = {'pending': 0, 'accepted': 0, 'rejected': 0}
    for bucket in contracts_qs.values('status').annotate(total=Count('id')):
        status_key = bucket['status']
        group = status_styles.get(status_key, {}).get('group')
        if group in status_totals:
            status_totals[group] += bucket['total']

    upcoming_orders = []
    pending_orders = []
    past_orders = []

    for contract in contracts_qs:
        status_config = status_styles.get(
            contract.status,
            {
                'badge_classes': 'bg-gray-100 text-gray-600',
                'dot_classes': 'bg-gray-400',
                'label': contract.status.title(),
            },
        )

        price_value = contract.price if contract.price is not None else contract.service.price

        if user.is_provider:
            counterpart = contract.user
            counterpart_label = 'Cliente'
            counterpart_name = counterpart.get_full_name() or counterpart.username
        else:
            counterpart = contract.service.provider
            counterpart_label = 'Profesional'
            counterpart_name = counterpart.get_full_name() or counterpart.username

        order_data = {
            'id': contract.id,
            'service_id': contract.service.id,
            'service_name': contract.service.name,
            'counterpart_label': counterpart_label,
            'counterpart_name': counterpart_name,
            'counterpart_id': counterpart.id,
            'status': contract.status,
            'status_label': status_config['label'],
            'badge_classes': status_config['badge_classes'],
            'dot_classes': status_config['dot_classes'],
            'start_date': contract.start_date,
            'created_at': contract.created_at,
            'price': price_value,
            'has_price': price_value is not None,
            'detail_url': reverse('service_detail', args=[contract.service.id]),
            'service_description': contract.service.description,
            'code': contract.code,
            'can_manage': user.is_provider and contract.status == 'pending',
        }

        if contract.status in ['accepted', 'active']:
            upcoming_orders.append(order_data)
        elif contract.status in ['pending', 'paused']:
            pending_orders.append(order_data)
        else:  # rejected, cancelled, finished
            past_orders.append(order_data)

    context = {
        'upcoming_orders': upcoming_orders,
        'pending_orders': pending_orders,
        'past_orders': past_orders,
        'is_provider': user.is_provider,
        'pending_orders_count': status_totals['pending'],
        'accepted_orders_count': status_totals['accepted'],
        'rejected_orders_count': status_totals['rejected'],
    }
    return render(request, 'my_orders.html', context)


@login_required
def profile(request):
    user = request.user

    # Get or create user profile
    profile, _ = CustomUser.objects.get_or_create(username=user)

    # Avatar URL (fallback a una imagen estática si no hay)
    avatar_url = profile.avatar.url if getattr(profile, "avatar", None) else static('images/user-icon.png')

    # Services (paginated)
    services_list = Service.objects.filter(provider=user).order_by('-created_at')
    services_paginator = Paginator(services_list, 5)
    services_page = request.GET.get('services_page')
    user_services = services_paginator.get_page(services_page)

    # Contracts (paginated)
    contracts_list = Contract.objects.filter(user=user).order_by('-created_at')
    contracts_paginator = Paginator(contracts_list, 5)
    contracts_page = request.GET.get('contracts_page')
    user_contracts = contracts_paginator.get_page(contracts_page)

    # Reviews received
    user_reviews = Review.objects.filter(service__provider=user).order_by('-created_at')

    # Stats
    services_count = services_list.count()
    contracts_count = contracts_list.count()
    reviews_count = user_reviews.count()
    average_rating = user_reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    # Unread notifications
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()

    context = {
        'user': user,
        'profile': profile,
        'avatar_url': avatar_url,
        'user_services': user_services,
        'user_contracts': user_contracts,
        'user_reviews': user_reviews[:3],
        'services_count': services_count,
        'contracts_count': contracts_count,
        'reviews_count': reviews_count,
        'average_rating': average_rating,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    profile, created = CustomUser.objects.get_or_create(username=request.user)

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
        profile.profession = request.POST.get('profession', '')

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


@login_required
def chat_list_view(request):
    """
    Vista para la "bandeja de entrada" (chat_list.html).
    Muestra todas las conversaciones del usuario logueado.
    """
    conversations_qs = Conversation.objects.filter(participants=request.user)

    context_conversations = []

    for conv in conversations_qs:
        otro_usuario = conv.get_other_participant(request.user)
        ultimo_mensaje = conv.messages.order_by('-timestamp').first()
        no_leidos = conv.messages.filter(is_read=False).exclude(sender=request.user).count()

        context_conversations.append({
            'conversation_obj': conv,
            'otro_usuario': otro_usuario,
            'ultimo_mensaje': ultimo_mensaje,
            'no_leidos': no_leidos,
        })

    context_conversations.sort(
        key=lambda x: x['ultimo_mensaje'].timestamp if x['ultimo_mensaje'] else x['conversation_obj'].created_at,
        reverse=True
    )

    # Paginación manual de la lista ordenada
    paginator = Paginator(context_conversations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'chats.html', {
        'conversations': page_obj,
        'page_obj': page_obj
    })


@login_required
def chat_detail_view(request, conversation_id):
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
        otro_usuario = conversation.participants.exclude(id=request.user.id).first()

    except Exception as e:
        print(f"Error al cargar chat: {e}")
        return redirect('chats')

    if request.method == "POST":
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            return redirect('chat_detail', conversation_id=conversation_id)

    context = {
        'messages': messages,
        'conversation_id': conversation_id,
        'otro_usuario': otro_usuario,
        'conversation': conversation,
    }
    return render(request, 'chat_detail.html', context)


@login_required
def get_new_messages(request, conversation_id):
    """
    Esta es la vista de API que el JavaScript llama cada 3 segundos.
    Devuelve mensajes nuevos en formato JSON.
    """

    since_timestamp_str = request.GET.get('since')

    try:
        conversation = Conversation.objects.get(id=conversation_id, participants=request.user)
        messages = Message.objects.filter(conversation=conversation)

    except Conversation.DoesNotExist:
        return JsonResponse({"error": "No autorizado o no encontrado"}, status=403)

    if since_timestamp_str:
        try:
            since_timestamp = parse_datetime(since_timestamp_str)
            if since_timestamp:
                messages = messages.filter(timestamp__gt=since_timestamp)
        except ValueError:
            pass

    messages = messages.order_by('timestamp')

    new_messages_data = [
        {
            'id': message.id,
            'sender_id': message.sender.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),  # Envía en formato ISO
        }
        for message in messages
    ]

    return JsonResponse(new_messages_data, safe=False)


@login_required
@allowed_roles(CustomUser.Roles.PROVIDER, CustomUser.Roles.FREELANCER, CustomUser.Roles.COMPANY_ADMIN)
def my_services(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        price_str = request.POST.get('price')
        cover_images = request.FILES.getlist('cover_images')  # Cambiado a plural
        category_ids = request.POST.getlist('categories')
        service_id = request.POST.get('service_id')

        if not name or not price_str:
            messages.error(request, 'El nombre y el precio son obligatorios.')
            return redirect('my_services')

        try:
            price = float(price_str)
        except ValueError:
            messages.error(request, 'El precio debe ser un número válido.')
            return redirect('my_services')

        if service_id:
            # EDITAR SERVICIO EXISTENTE
            try:
                service = Service.objects.get(id=service_id, provider=request.user)
                service.name = name
                service.description = description
                service.price = price

                # Eliminar imágenes marcadas
                images_to_delete_ids = request.POST.getlist('delete_images')
                if images_to_delete_ids:
                    ServiceImage.objects.filter(id__in=images_to_delete_ids, service=service).delete()

                # Agregar nuevas imágenes
                for f in cover_images:
                    ServiceImage.objects.create(service=service, image=f)

                service.save()

                # Actualizar categorías
                if category_ids:
                    service.categories.set(category_ids)
                else:
                    service.categories.clear()

                # Verificar que tenga al menos una imagen
                if service.images.count() == 0:
                    messages.error(request, 'El servicio debe tener al menos una imagen.')
                    return redirect('my_services')

                messages.success(request, 'Servicio actualizado correctamente.')

            except Service.DoesNotExist:
                messages.error(request, 'Servicio no encontrado.')
        else:
            # CREAR NUEVO SERVICIO
            if not cover_images:
                messages.error(request, 'Debes subir al menos una imagen.')
                return redirect('my_services')

            new_service = Service.objects.create(
                provider=request.user,
                name=name,
                description=description,
                price=price
            )

            # Agregar imágenes
            for f in cover_images:
                ServiceImage.objects.create(service=new_service, image=f)

            # Agregar categorías
            if category_ids:
                new_service.categories.set(category_ids)

            messages.success(request, 'Servicio creado correctamente.')

        return redirect('my_services')

    # GET request
    user_services_list = Service.objects.filter(provider=request.user).prefetch_related('images', 'categories').order_by(
        '-created_at')
    
    paginator = Paginator(user_services_list, 10)
    page_number = request.GET.get('page')
    user_services = paginator.get_page(page_number)

    all_categories = Category.objects.all()

    context = {
        'services': user_services,
        'page_obj': user_services,
        'categories': all_categories,
    }
    return render(request, 'my_services.html', context)


@login_required
def delete_service(request, service_id):
    service = get_object_or_404(Service, id=service_id, provider=request.user)

    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Servicio eliminado correctamente.')

    return redirect('my_services')


@login_required
def toggle_favorite(request, service_id):
    """
    Vista para añadir/quitar un servicio de favoritos.
    Devuelve JSON con el estado del favorito.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    service = get_object_or_404(Service, id=service_id)

    try:
        # Intentar obtener el favorito existente
        favorite = Favorite.objects.filter(user=request.user, service=service).first()

        if favorite:
            # Si existe, eliminarlo
            favorite_id = favorite.id
            favorite.delete()
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': 'Servicio eliminado de favoritos'
            })
        else:
            # Si no existe, crearlo
            favorite = Favorite.objects.create(user=request.user, service=service)
            return JsonResponse({
                'success': True,
                'action': 'added',
                'favorite_id': favorite.id,
                'message': 'Servicio añadido a favoritos'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def public_profile(request, username):
    """
    Muestra el perfil público de un usuario, sus servicios y reseñas.
    """
    # 1. Obtener el usuario y su perfil
    try:
        user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        # Aquí podrías redirigir a una página 404
        messages.error(request, "El usuario no existe.")
        return redirect('home')

    profile, _ = CustomUser.objects.get_or_create(username=user)

    # 2. Obtener los servicios de este usuario
    services_list = Service.objects.filter(provider=user).prefetch_related('images', 'categories').order_by('-created_at')
    
    paginator = Paginator(services_list, 6)
    page_number = request.GET.get('page')
    services = paginator.get_page(page_number)

    # 3. Obtener las reseñas recibidas por este usuario (en cualquiera de sus servicios)
    reviews = Review.objects.filter(service__provider=user).select_related('user').order_by(
        '-created_at')

    # 4. Calcular estadísticas
    reviews_count = reviews.count()
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    total_services_count = services_list.count()

    # 5. Obtener favoritos del usuario actual
    user_favorites = {}
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user).values('service_id', 'id')
        user_favorites = {fav['service_id']: fav['id'] for fav in favorites}

    context = {
        'profile_user': user,
        'profile': profile,
        'services': services,
        'page_obj': services,
        'reviews': reviews,
        'reviews_count': reviews_count,
        'average_rating': average_rating,
        'total_services_count': total_services_count,
        'user_favorites_json': json.dumps(user_favorites),
    }

    return render(request, 'public_profile.html', context)


def service_detail(request, service_id):
    """
    Muestra la página de detalle de un servicio.
    """
    service = get_object_or_404(
        Service.objects.select_related('provider')
        .prefetch_related('images', 'categories'),
        id=service_id
    )

    # Obtener reviews y estadísticas
    reviews = Review.objects.filter(service=service).select_related('user').order_by('-created_at')

    stats = reviews.aggregate(
        average_rating=Avg('rating'),
        reviews_count=Count('id')
    )

    average_rating = stats.get('average_rating') or 0
    reviews_count = stats.get('reviews_count') or 0

    # Obtener estadísticas GLOBALES del proveedor
    provider = service.provider
    provider_reviews = Review.objects.filter(service__provider=provider)
    provider_stats = provider_reviews.aggregate(
        total_avg_rating=Avg('rating'),
        total_reviews_count=Count('id')
    )
    provider_avg_rating = provider_stats.get('total_avg_rating') or 0
    provider_reviews_count = provider_stats.get('total_reviews_count') or 0

    # Verificar si el usuario ya tiene un contrato activo/pendiente para este servicio
    existing_contract = None
    if request.user.is_authenticated:
        existing_contract = Contract.objects.filter(
            user=request.user,
            service=service,
            status__in=['pending', 'accepted', 'active']
        ).first()

    context = {
        'service': service,
        'reviews': reviews,
        'average_rating': average_rating,
        'reviews_count': reviews_count,
        'provider_avg_rating': provider_avg_rating,
        'provider_reviews_count': provider_reviews_count,
        'existing_contract': existing_contract,
    }
    return render(request, 'service_detail.html', context)


@login_required
def start_chat(request, service_id):
    """
    Busca o crea una conversación con el proveedor de un servicio
    y redirige a la sala de chat.
    """
    service = get_object_or_404(Service, id=service_id)
    provider = service.provider
    user = request.user

    # No puedes chatear contigo mismo
    if provider == user:
        messages.error(request, "No puedes contactar contigo mismo.")
        return redirect('service_detail', service_id=service.id)

    # Buscar conversación existente entre los dos participantes
    # Usamos Q para buscar participantes en cualquier orden
    conversation = Conversation.objects.filter(participants=user).filter(participants=provider).first()

    if conversation:
        # Ya existe una conversación, redirigir a ella
        return redirect('chat_detail', conversation_id=conversation.id)
    else:
        # Crear una nueva conversación
        new_convo = Conversation.objects.create()
        new_convo.participants.add(user, provider)
        new_convo.save()
        return redirect('chat_detail', conversation_id=new_convo.id)


def start_chat_order(request, contract_id):
    """
    Inicia un chat desde un pedido/contrato.
    Identifica automáticamente quién es el interlocutor.
    """
    contract = get_object_or_404(Contract, id=contract_id)
    user = request.user
    
    # Determinar el interlocutor
    if user == contract.service.provider:
        counterpart = contract.user
    elif user == contract.user:
        counterpart = contract.service.provider
    else:
        messages.error(request, "No tienes permiso para acceder a este chat.")
        return redirect('my_orders')

    # Buscar conversación existente
    conversation = Conversation.objects.filter(participants=user).filter(participants=counterpart).first()

    if conversation:
        return redirect('chat_detail', conversation_id=conversation.id)
    else:
        new_convo = Conversation.objects.create()
        new_convo.participants.add(user, counterpart)
        new_convo.save()
        return redirect('chat_detail', conversation_id=new_convo.id)


@login_required
def request_service(request, service_id):
    """
    Procesa la solicitud de contratación de un servicio.
    Crea un contrato en estado 'pending'.
    """
    if request.method != 'POST':
        return redirect('service_detail', service_id=service_id)

    service = get_object_or_404(Service, id=service_id)
    
    # No puedes contratar tu propio servicio
    if service.provider == request.user:
        messages.error(request, "No puedes contratar tu propio servicio.")
        return redirect('service_detail', service_id=service_id)

    # Verificar duplicados
    existing = Contract.objects.filter(
        user=request.user,
        service=service,
        status__in=['pending', 'accepted', 'active']
    ).exists()

    if existing:
        messages.warning(request, "Ya tienes una solicitud activa para este servicio.")
        return redirect('service_detail', service_id=service_id)

    start_date = request.POST.get('start_date')
    start_time = request.POST.get('start_time')
    description = request.POST.get('description')

    if not start_date or not start_time:
        messages.error(request, "Debes seleccionar fecha y hora.")
        return redirect('service_detail', service_id=service_id)

    try:
        contract = Contract.objects.create(
            user=request.user,
            service=service,
            start_date=start_date,
            start_time=start_time,
            description=description,
            status='pending',
            price=service.price  # Guardamos el precio actual
        )
        
        # Crear notificación para el proveedor
        create_notification(
            user=service.provider,
            title="Nueva solicitud de servicio",
            message=f"{request.user.get_full_name() or request.user.username} ha solicitado contratar '{service.name}'.",
            notification_type='contract_update'
        )
        
        messages.success(request, "Solicitud enviada correctamente. El profesional revisará tu petición.")
        return redirect('my_orders')
        
    except Exception as e:
        messages.error(request, f"Error al procesar la solicitud: {str(e)}")
        return redirect('service_detail', service_id=service_id)



@login_required
def cancel_contract(request, contract_id):
    """
    Permite a un cliente cancelar un contrato pendiente o aceptado.
    Notifica al proveedor de la cancelación.
    """
    if request.method != 'POST':
        return redirect('my_orders')
    
    contract = get_object_or_404(Contract, id=contract_id)
    
    # Validar permisos usando el método del modelo
    if not contract.can_be_cancelled_by(request.user):
        messages.error(request, 'No puedes cancelar este contrato. Solo se pueden cancelar contratos pendientes o aceptados.')
        return redirect('my_orders')
    
    cancellation_reason = request.POST.get('cancellation_reason', '')
    
    try:
        contract.status = 'cancelled'
        contract.cancellation_reason = cancellation_reason
        contract.save(update_fields=['status', 'cancellation_reason'])
        
        # Determinar a quién notificar
        if request.user == contract.user:
            # El cliente canceló, notificar al proveedor
            notify_user = contract.service.provider
            title = "Contrato cancelado por cliente"
            message = f"El cliente {request.user.get_full_name() or request.user.username} ha cancelado su solicitud para '{contract.service.name}'. Motivo: {cancellation_reason}"
        else:
            # El proveedor canceló, notificar al cliente
            notify_user = contract.user
            title = "Contrato cancelado por profesional"
            message = f"El profesional {request.user.get_full_name() or request.user.username} ha cancelado el servicio '{contract.service.name}'. Motivo: {cancellation_reason}"

        create_notification(
            user=notify_user,
            title=title,
            message=message,
            notification_type='contract_cancelled',
            contract=contract
        )
        
        messages.success(request, 'Has cancelado el contrato correctamente. La otra parte será notificada.')
        
    except Exception as e:
        messages.error(request, f'Error al cancelar el contrato: {str(e)}')
    
    return redirect('my_orders')


@login_required
def provider_agenda(request):
    """
    Vista de agenda para proveedores.
    Muestra los servicios aceptados futuros ordenados cronológicamente.
    """
    if not request.user.is_provider:
        messages.error(request, "Acceso no autorizado.")
        return redirect('home')

    today = timezone.now().date()
    
    # Obtener contratos aceptados desde hoy en adelante
    upcoming_contracts = Contract.objects.filter(
        service__provider=request.user,
        status='accepted',
        start_date__gte=today
    ).select_related('user', 'service').order_by('start_date', 'start_time')

    context = {
        'upcoming_contracts': upcoming_contracts,
    }
    return render(request, 'provider_agenda.html', context)

