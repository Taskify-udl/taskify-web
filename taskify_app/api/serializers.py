from rest_framework import serializers
from taskify_app.models import Category, Service, ServiceCategory, Contract, Review, Favorite


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class ServiceSerializer(serializers.ModelSerializer):
    # El provider lo fija el servidor (request.user) en perform_create
    provider = serializers.PrimaryKeyRelatedField(read_only=True)
    # categorías como lista de IDs
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all(), required=False
    )

    class Meta:
        model = Service
        fields = ("id", "name", "description", "provider", "categories", "created_at", "updated_at")
        read_only_fields = ("provider", "created_at", "updated_at")

    def update(self, instance, validated_data):
        # impedir cambiar el provider vía API
        validated_data.pop("provider", None)
        return super().update(instance, validated_data)


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ("id", "service", "category")


class ContractSerializer(serializers.ModelSerializer):
    # UUID se genera solo y el user lo fija el servidor
    code = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Contract
        fields = ("id", "code", "user", "service", "start_date", "status", "price", "created_at")
        read_only_fields = ("code", "user", "created_at")

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        return super().update(instance, validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "service", "rating", "comment", "created_at", "updated_at")
        read_only_fields = ("user", "created_at", "updated_at")

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        return super().update(instance, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "user", "service", "favorited_at")
        read_only_fields = ("user", "favorited_at")

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        return super().update(instance, validated_data)
