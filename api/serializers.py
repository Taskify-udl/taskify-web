from rest_framework import serializers
from django.contrib.auth.models import User
from taskify_app.models import Category, Service


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username', 'email', 'password']


class ServiceSerializer(serializers.ModelSerializer):
    provider = serializers.PrimaryKeyRelatedField(read_only=True)
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