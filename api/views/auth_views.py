from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework. decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from api.serializers import UserSerializer
from django.contrib.auth.models import User


@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username'])
    if not user.check_password(request.data['password']):
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
    token, created = Token.objects.get_or_create(user=user)

    user_data = UserSerializer(user).data
    user_data.pop('password', None)
    return Response({"token": token.key, "user": user_data}, status=status.HTTP_200_OK)

@api_view(['POST'])
def register(request):
    print(request.data)
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        user = User.objects.get(username=request.data['username'])
        print(serializer.data)
        user.set_password(serializer.data['password'])
        user.save()

        user_data = serializer.data
        user_data.pop('password', None)
        token = Token.objects.create(user=user)
        return Response({"token": token.key, "user": user_data}, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile(request):
    print(request.user)
    return Response({"profile"})
