from django.contrib.auth.models import User
from rest_framework import serializers

from nutri.models import Dieta, ImprimirDieta


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_active", "is_staff", "date_joined")
        read_only_fields = fields


class DietaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dieta
        fields = "__all__"
        read_only_fields = ("usuario",)


class ImprimirDietaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImprimirDieta
        fields = "__all__"
        read_only_fields = ("usuario",)


