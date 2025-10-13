from multiprocessing import Value
from sqlite3 import IntegrityError

from django.db.models import When, Q
from django.forms import IntegerField
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework. decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from sqlparse.sql import Case
from urllib3 import request

from api.serializers import ServiceSerializer
from taskify_app.models import Service


@api_view(['POST', 'GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def services(request):
    if request.method == 'GET':
        search = request.query_params.get('search', '').strip()

        qs = Service.objects.all()

        if search:
            # Filtra por nombre o descripción
            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            ).annotate(
                # Añade un campo de prioridad: 1 si el nombre contiene el término, 0 en caso contrario
                priority=Case(
                    When(name__icontains=search, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by('-priority', 'name')  # primero los que coinciden en nombre

        serializer = ServiceSerializer(qs, many=True)
        return Response(serializer.data)

    data = request.data.copy()
    data.pop('id', None)

    serializer = ServiceSerializer(data=data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    obj = serializer.save(provider=request.user)
    return Response(ServiceSerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def service_detail(request, pk: int):
    service = get_object_or_404(Service, pk=pk)

    # Autorización: solo el provider (o adapta si quieres admins)

    if request.method == 'GET':
        return Response(ServiceSerializer(service).data)

    if request.method in ('PUT', 'PATCH'):
        if service.provider_id != request.user.id:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        data = request.data.copy()
        data.pop('id', None)          # no permitimos tocar el id
        data.pop('provider', None)    # ni cambiar el provider

        serializer = ServiceSerializer(
            service,
            data=data,
            partial=(request.method == 'PATCH'),
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        obj = serializer.save()  # provider queda intacto (read_only en el serializer)
        return Response(ServiceSerializer(obj).data, status=status.HTTP_200_OK)

    # DELETE
    if service.provider_id != request.user.id:
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    service.delete()
    return Response({'detail': 'service deleted'},status=status.HTTP_204_NO_CONTENT)
