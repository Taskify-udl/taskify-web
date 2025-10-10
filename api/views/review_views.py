from sqlite3 import IntegrityError

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from taskify_app.models import Review, Service
from api.serializers import ReviewSerializer


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def reviews(request):
    """
    Colección de reviews:
      - GET: lista (filtrable por ?service=<id>, ?user=<id>, ?search=<texto>)
      - POST: crear (user se asigna del request, service por ID en el payload)
    """
    if request.method == 'GET':
        search = request.query_params.get('search', '').strip()
        service_id = request.query_params.get('service')
        user_id = request.query_params.get('user')

        qs = Review.objects.select_related('user', 'service').all()

        if service_id:
            qs = qs.filter(service_id=service_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if search:
            qs = qs.filter(Q(comment__icontains=search))

        serializer = ReviewSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # POST (crear)
    data = request.data.copy()
    data.pop('id', None)
    data.pop('user', None)      # lo fija el backend
    # service se acepta por ID en el serializer

    serializer = ReviewSerializer(data=data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        obj = serializer.save(user=request.user)
    except IntegrityError:
        # cubre unique_together (user, service)
        return Response(
            {'detail': 'Ya has creado una reseña para este servicio.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(ReviewSerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def review_detail(request, pk: int):
    """
    Detalle de una review:
      - GET: ver
      - PUT/PATCH: editar (solo autor)
      - DELETE: borrar (solo autor)
    """
    review = get_object_or_404(Review.objects.select_related('user', 'service'), pk=pk)

    if request.method == 'GET':
        return Response(ReviewSerializer(review).data)

    # Solo el autor puede modificar/eliminar
    if review.user_id != request.user.id:
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ('PUT', 'PATCH'):
        data = request.data.copy()
        data.pop('id', None)
        data.pop('user', None)     # no se puede cambiar el autor
        data.pop('service', None)  # no se puede mover a otro servicio

        serializer = ReviewSerializer(
            review,
            data=data,
            partial=(request.method == 'PATCH'),
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            obj = serializer.save()
        except IntegrityError:
            return Response(
                {'detail': 'Conflicto de unicidad (user, service).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(ReviewSerializer(obj).data, status=status.HTTP_200_OK)

    # DELETE
    review.delete()
    return Response({'detail': 'review deleted'}, status=status.HTTP_204_NO_CONTENT)
