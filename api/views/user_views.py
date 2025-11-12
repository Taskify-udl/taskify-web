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

from api.serializers import UserProfileSerializer


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