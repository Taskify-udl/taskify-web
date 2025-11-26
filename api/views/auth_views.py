from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from api.serializers import UserSerializer
from django.contrib.auth.models import User

from taskify_app.models import CustomUser


@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = get_object_or_404(CustomUser, username=username)

    if not user.check_password(password):
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST
        )

    token, created = Token.objects.get_or_create(user=user)

    user_data = UserSerializer(user).data
    user_data.pop('password', None)  # por si acaso

    user_data['role'] = user.role

    return Response(
        {
            "token": token.key,
            "user": user_data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()

    token = Token.objects.create(user=user)

    return Response(
        {
            "token": token.key,
            "user": serializer.data
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile(request):
    return Response({"profile"})
