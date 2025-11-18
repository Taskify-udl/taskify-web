# core/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings


def allowed_roles(*allowed_roles):
    """
    Uso:
    @allowed_roles(CustomUser.Roles.PROVIDER)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            # Si no está autenticado > al login
            if not user.is_authenticated:
                return redirect(settings.LOGIN_URL)

            # Superuser siempre puede entrar
            if getattr(user, "is_superuser", False):
                return view_func(request, *args, **kwargs)

            # Role del usuario
            user_role = getattr(user, "role", None)

            if user_role not in allowed_roles:
                messages.error(request, "No tienes permiso para acceder a esta página.")
                return redirect('home')  # <-- aquí redirige al home

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
