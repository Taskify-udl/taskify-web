from sqlite3 import IntegrityError

from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from api.serializers import CategorySerializer
from taskify_app.models import Category


def _require_staff(user):
    return user.is_staff or user.is_superuser


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def categories(request):
    """
    Colección de categorías:
      - GET: lista (filtro ?search=<texto>)
      - POST: crear (solo staff/superuser)
    """
    if request.method == 'GET':
        search = request.query_params.get('search', '').strip()

        qs = Category.objects.all()

        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        # opcional: devolver cuántos servicios hay en cada categoría
        qs = qs.annotate(service_count=Count('services'))

        serializer = CategorySerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # POST
    if not _require_staff(request.user):
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data.copy()
    data.pop('id', None)

    serializer = CategorySerializer(data=data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        obj = serializer.save()
    except IntegrityError:
        return Response({'detail': 'Nombre o slug ya existente.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(CategorySerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def category_detail(request, pk: int):
    """
    Detalle de una categoría:
      - GET: ver
      - PUT/PATCH: editar (solo staff/superuser)
      - DELETE: borrar (solo staff/superuser)
    """
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'GET':
        return Response(CategorySerializer(category).data)

    if not _require_staff(request.user):
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ('PUT', 'PATCH'):
        data = request.data.copy()
        data.pop('id', None)

        serializer = CategorySerializer(
            category,
            data=data,
            partial=(request.method == 'PATCH'),
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            obj = serializer.save()
        except IntegrityError:
            return Response({'detail': 'Nombre o slug ya existente.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(CategorySerializer(obj).data, status=status.HTTP_200_OK)

    # DELETE
    category.delete()
    return Response({'detail': 'category deleted'}, status=status.HTTP_204_NO_CONTENT)
