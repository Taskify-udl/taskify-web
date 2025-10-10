from sqlite3 import IntegrityError

from django.db.models import Q, When, Value, IntegerField
from django.db.models import Case as DJCase
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from taskify_app.models import Favorite, Service
from api.serializers import ServiceSerializer, FavoriteSerializer


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def favorites(request):
    """
    Colección de favoritos:
      - GET: lista los servicios marcados como favoritos por el usuario autenticado.
      - POST: crea un nuevo favorito ({"service": <id>}).
    """
    user = request.user

    if request.method == 'GET':
        search = request.query_params.get('search', '').strip()

        qs = (
            Service.objects
            .filter(favorited_by__user=user)
            .prefetch_related('categories')
            .all()
        )

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search)) \
                   .annotate(
                       priority=DJCase(
                           When(name__icontains=search, then=Value(1)),
                           default=Value(0),
                           output_field=IntegerField(),
                       )
                   ) \
                   .order_by('-priority', 'name')
        else:
            qs = qs.order_by('name')

        serializer = ServiceSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # POST: crear favorito
    service_id = request.data.get('service')
    if not service_id:
        return Response({'service': ['Este campo es obligatorio.']}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fav, created = Favorite.objects.get_or_create(user=user, service_id=service_id)
    except IntegrityError:
        return Response({'detail': 'Ya es favorito.'}, status=status.HTTP_200_OK)

    # devolvemos el Favorite, no el Service
    serializer = FavoriteSerializer(fav, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def favorite_detail(request, pk: int):
    """
    DELETE /favorite/<id>
    Elimina un favorito concreto (solo el propietario puede hacerlo).
    """
    favorite = Favorite.objects.filter(pk=pk, user=request.user).first()
    if not favorite:
        return Response({'detail': 'No encontrado o no autorizado.'}, status=status.HTTP_404_NOT_FOUND)

    favorite.delete()
    return Response({'detail': 'favorite deleted'}, status=status.HTTP_204_NO_CONTENT)
