from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import ReadOnly, IsProvider, IsAdmin, IsOwnerOrAdmin
from .serializers import *
from ..models import Category, Service, Contract, Review, Favorite, ServiceCategory


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer

    def get_permissions(self):
        # Lectura pública; crear/editar/borrar solo admin autenticado
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all().order_by("name")
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]  # 👈 público
        elif self.action == "create":
            return [IsAuthenticated(), IsProvider()]  # solo provider logeado
        else:  # update/partial_update/destroy
            return [IsAuthenticated(), IsOwnerOrAdmin()]  # dueño o admin

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.select_related("user", "service").all()
    serializer_class = ContractSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]  # 👈 ver contratos exige login
        else:
            return [IsAuthenticated(), IsOwnerOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related("user", "service").all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]  # reseñas visibles a todos
        return [IsAuthenticated(), IsOwnerOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.select_related("user", "service").all()
    serializer_class = FavoriteSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]  # ver favoritos exige login
        return [IsAuthenticated(), IsOwnerOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.select_related("service", "category").all()
    serializer_class = ServiceCategorySerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]  # tocar la puente, solo admin
