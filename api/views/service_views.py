from django.db.models import Case, When, Value, IntegerField, Q  # <--- Importaciones corregidas
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from sqlparse.sql import Case

from api.serializers import ServiceSerializer
from taskify_app.models import Service, Category


@api_view(['GET', 'POST'])  # Es más limpio dejar PUT/DELETE para el service_detail
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def services(request):
    if request.method == 'GET':
        # --- 1. Obtener parámetros ---
        search = request.query_params.get('search', '').strip()
        category_id = request.query_params.get('category')  # ID de la categoría

        # Valores por defecto para paginación manual
        try:
            top = int(request.query_params.get('top', 20))  # Límite (default 20)
            skip = int(request.query_params.get('skip', 0))  # Salto (default 0)
        except ValueError:
            top = 20
            skip = 0

        qs = Service.objects.all()

        # --- 2. Filtro por Categoría ---
        if category_id:
            # Como es ManyToMany, usamos categories__id
            qs = qs.filter(categories__id=category_id)

        # --- 3. Buscador y Ordenamiento ---
        if search:
            # Filtra por nombre o descripción
            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            ).annotate(
                priority=Case(
                    When(name__icontains=search, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by('-priority', 'name')
        else:
            # Orden por defecto si no hay búsqueda (importante para la paginación consistente)
            qs = qs.order_by('-created_at')

        # --- 4. Paginación (Top & Skip) ---
        # Aplicamos el slicing al final. Esto traduce a LIMIT y OFFSET en SQL.
        # qs[skip : skip + top] -> desde el índice 'skip' hasta 'skip + top'
        qs = qs[skip: skip + top]

        serializer = ServiceSerializer(qs, many=True)

        # Opcional: Si quieres devolver metadata de paginación, cambia el return
        # return Response({'data': serializer.data, 'total': total_count})

        return Response(serializer.data)

    # --- Lógica del POST (Creación) se mantiene igual ---
    elif request.method == 'POST':
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
        data.pop('id', None)  # no permitimos tocar el id
        data.pop('provider', None)  # ni cambiar el provider

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
    return Response({'detail': 'service deleted'}, status=status.HTTP_204_NO_CONTENT)
