from rest_framework.permissions import BasePermission, SAFE_METHODS

def in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))

class IsProvider(BasePermission):
    def has_permission(self, request, view):
        return in_group(request.user, "provider") or request.user.is_staff or request.user.is_superuser

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

class IsOwnerOrAdmin(BasePermission):
    """Permite editar si es el 'dueño' del objeto (campo user/provider) o admin."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "provider", None) or getattr(obj, "user", None)
        return (request.user.is_authenticated
                and (owner == request.user or request.user.is_staff or request.user.is_superuser))
