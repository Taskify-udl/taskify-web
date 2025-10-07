from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .serializers import RegisterSerializer

@method_decorator(csrf_exempt, name="dispatch")  # evitar CSRF en POST anónimo
class   RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # no forzar autenticación en este endpoint

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "groups": list(user.groups.values_list("name", flat=True)),
        }

        # Si tienes JWT instalado, devuelve tokens
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            data["access"] = str(refresh.access_token)
            data["refresh"] = str(refresh)
        except Exception:
            # No hay simplejwt: devolvemos solo el usuario
            pass

        return Response(data, status=status.HTTP_201_CREATED)
