import uuid
from django.db.models import Q
from django.shortcuts import get_object_or_404
from sqlite3 import IntegrityError

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from taskify_app.models import Contract
from api.serializers import ContractSerializer


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def contracts(request):
    """
    Maneja la colección de contratos:
      - GET: listar (filtrable por ?service=<id>, ?status=<estado>)
      - POST: crear contrato (user se asigna automáticamente)
    """
    if request.method == 'GET':
        service_id = request.query_params.get('service')
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search', '').strip()

        qs = Contract.objects.select_related('user', 'service').all()

        if service_id:
            qs = qs.filter(service_id=service_id)
        if status_filter:
            qs = qs.filter(status__iexact=status_filter)
        if search:
            qs = qs.filter(Q(service__name__icontains=search) | Q(user__username__icontains=search))

        serializer = ContractSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # POST (crear contrato)
    data = request.data.copy()
    data.pop('id', None)
    data.pop('user', None)
    data.pop('code', None)  # se genera automáticamente

    serializer = ContractSerializer(data=data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        obj = serializer.save(user=request.user)
    except IntegrityError:
        return Response({'detail': 'Error al crear el contrato.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(ContractSerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def contract_detail(request, pk: int):
    """
    Maneja un contrato específico:
      - GET: ver detalles
      - PUT/PATCH: modificar (solo el usuario autor)
      - DELETE: cancelar contrato (solo autor)
    """
    contract = get_object_or_404(Contract.objects.select_related('user', 'service'), pk=pk)

    if request.method == 'GET':
        return Response(ContractSerializer(contract).data)

    # Autorización
    if contract.user_id != request.user.id:
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ('PUT', 'PATCH'):
        data = request.data.copy()
        data.pop('id', None)
        data.pop('user', None)
        data.pop('code', None)
        data.pop('service', None)  # no se permite mover de servicio

        serializer = ContractSerializer(
            contract,
            data=data,
            partial=(request.method == 'PATCH'),
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        obj = serializer.save()
        return Response(ContractSerializer(obj).data, status=status.HTTP_200_OK)

    # DELETE → se interpreta como cancelación
    contract.status = "cancelled"
    contract.save()
    return Response({'detail': 'contract cancelled'}, status=status.HTTP_200_OK)
