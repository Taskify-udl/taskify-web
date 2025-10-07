from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework. decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from urllib3 import request

from api.serializers import ServiceSerializer
from taskify_app.models import Service


@api_view(['POST', 'GET', 'PUT', 'DELETE'])
def services(request):
    print (request.GET.items())
    return Response({"services": "services"})

