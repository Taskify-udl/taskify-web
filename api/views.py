from rest_framework.response import Response
from rest_framework.decorators import api_view

from api.serializers import CategorySerializer
from taskify_app.models import Category


@api_view(['GET'])
def getData(request):
    categorys = Category.objects.all()
    serializer = CategorySerializer(categorys, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def addCategory(request):
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)
