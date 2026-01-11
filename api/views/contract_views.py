from django.db.models import Q
from django.shortcuts import get_object_or_404
from sqlite3 import IntegrityError

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from taskify_app.models import Contract, ServiceSession
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


# Nueva vista: devuelve los contratos donde el request.user es cliente o proveedor
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_contracts(request):
    """
    Devuelve todos los contratos en los que el usuario autenticado es
    - el cliente (`contract.user`) o
    - el proveedor del servicio (`contract.service.provider`).

    Usa el `ContractSerializer` existente.
    """
    qs = Contract.objects.select_related('user', 'service', 'service__provider').filter(
        Q(user=request.user) | Q(service__provider=request.user)
    )

    serializer = ContractSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


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
    if contract.service.provider.id != request.user.id and contract.user.id != request.user.id:
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
    contract.status = Contract.Status.CANCELLED
    contract.save()
    return Response({'detail': 'contract cancelled'}, status=status.HTTP_200_OK)


# --- Nuevas vistas API para verificar códigos (start/stop) ---
from django.utils import timezone


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def contract_start(request, contract_id: int):
    """
    Endpoint API para iniciar un contrato usando `start_code_alpha` o `start_token`.
    Body aceptado:
      - { "code": "ABCDEF" }  (o "start_code_alpha": "ABCDEF")
      - { "token": "hex..." } (o "start_token": "hex...")
    Solo el cliente (contract.user) puede verificar el código/token.
    """
    contract = get_object_or_404(Contract.objects.select_related('user', 'service'), pk=contract_id)

    # Only the client can verify codes
    if request.user != contract.user:
        return Response({'success': False, 'message': 'Solo el cliente puede verificar los códigos.'}, status=status.HTTP_403_FORBIDDEN)

    # Obtener posibles campos del body
    provided_token = (request.data.get('token') or request.data.get('start_token') or '')
    # raw_code_field recoge lo que venga en 'code' o 'start_code_alpha' (sin normalizar)
    raw_code_field = request.data.get('code') or request.data.get('start_code_alpha') or ''

    provided_token = str(provided_token).strip()
    provided_code = str(raw_code_field).strip().upper()

    # Si sólo se pasa 'code' y ese valor corresponde al token, aceptarlo también
    token_from_code_field = ''
    if raw_code_field and not provided_token:
        token_from_code_field = str(raw_code_field).strip()

    if not provided_token and not provided_code:
        return Response({'success': False, 'message': 'Falta el código o token.'}, status=status.HTTP_400_BAD_REQUEST)

    match_token = False
    # Normalizar token a minúsculas para comparación tolerante a mayúsculas
    contract_token = (contract.start_token or '').strip()
    if provided_token:
        match_token = provided_token.strip().lower() == contract_token.lower()
    elif token_from_code_field:
        match_token = token_from_code_field.strip().lower() == contract_token.lower()

    match_code = provided_code and (provided_code == (contract.start_code_alpha or '').upper())

    if match_token or match_code:
        contract.actual_start = timezone.now()
        contract.status = Contract.Status.ACTIVE
        contract.save()
        # Create first session
        ServiceSession.objects.create(contract=contract)
        serializer = ContractSerializer(contract, context={'request': request})
        return Response({'success': True, 'message': 'Servicio iniciado correctamente.', 'contract': serializer.data}, status=status.HTTP_200_OK)

    return Response({'success': False, 'message': 'Código o token de inicio incorrecto.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def contract_stop(request, contract_id: int):
    """
    Endpoint API para finalizar un contrato usando `end_code_alpha` o `end_token`.
    Body aceptado:
      - { "code": "ABCDEF" }  (o "end_code_alpha": "ABCDEF")
      - { "token": "hex..." } (o "end_token": "hex...")
    Solo el cliente (contract.user) puede verificar el código/token.
    """
    contract = get_object_or_404(Contract.objects.select_related('user', 'service'), pk=contract_id)

    # Only the client can verify codes
    if request.user != contract.user:
        return Response({'success': False, 'message': 'Solo el cliente puede verificar los códigos.'}, status=status.HTTP_403_FORBIDDEN)

    # Obtener posibles campos del body
    provided_token = (request.data.get('token') or request.data.get('end_token') or '')
    raw_code_field = request.data.get('code') or request.data.get('end_code_alpha') or ''

    provided_token = str(provided_token).strip()
    provided_code = str(raw_code_field).strip().upper()

    token_from_code_field = ''
    if raw_code_field and not provided_token:
        token_from_code_field = str(raw_code_field).strip()

    if not provided_token and not provided_code:
        return Response({'success': False, 'message': 'Falta el código o token.'}, status=status.HTTP_400_BAD_REQUEST)

    match_token = False
    # Normalizar token a minúsculas para comparación tolerante a mayúsculas
    contract_end_token = (contract.end_token or '').strip()
    if provided_token:
        match_token = provided_token.strip().lower() == contract_end_token.lower()
    elif token_from_code_field:
        match_token = token_from_code_field.strip().lower() == contract_end_token.lower()

    match_code = provided_code and (provided_code == (contract.end_code_alpha or '').upper())

    if match_token or match_code:
        contract.actual_end = timezone.now()
        contract.status = Contract.Status.FINISHED
        contract.save()
        # Close active session
        active_session = contract.sessions.filter(end_time__isnull=True).last()
        if active_session:
            active_session.end_time = timezone.now()
            active_session.save()
        serializer = ContractSerializer(contract, context={'request': request})
        return Response({'success': True, 'message': 'Servicio finalizado correctamente.', 'show_review_modal': True, 'contract': serializer.data}, status=status.HTTP_200_OK)

    return Response({'success': False, 'message': 'Código o token de finalización incorrecto.'}, status=status.HTTP_400_BAD_REQUEST)
