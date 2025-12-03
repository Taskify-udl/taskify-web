from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    parser_classes,
)
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from api.serializers import UserProfileSerializer, ChangePasswordSerializer


@api_view(["GET", "PUT", "PATCH"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile_detail(request):
    user = request.user

    if request.method == "GET":
        serializer = UserProfileSerializer(user, context={"request": request})
        return Response(serializer.data)

    # Distinción explícita entre PUT (reemplazo completo) y PATCH (parcial)
    if request.method == "PUT":
        partial = False
    else:  # PATCH
        partial = True

    serializer = UserProfileSerializer(user, data=request.data, partial=partial, context={"request": request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    obj = serializer.save()
    return Response(UserProfileSerializer(obj, context={"request": request}).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)

    if serializer.is_valid():
        user = request.user
        old_password = serializer.data.get("old_password")
        new_password = serializer.data.get("new_password")

        # Verificar si la contraseña actual es correcta
        if not user.check_password(old_password):
            return Response(
                {"old_password": ["La contraseña actual es incorrecta."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Establecer la nueva contraseña y guardar
        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)