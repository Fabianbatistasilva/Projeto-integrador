from django.contrib.auth.models import User
from rest_framework import filters, permissions, viewsets

from nutri.models import Dieta, ImprimirDieta
from nutri.serializers import DietaSerializer, ImprimirDietaSerializer, UserSerializer


class DietaViewSet(viewsets.ModelViewSet):
    queryset = Dieta.objects.all()
    serializer_class = DietaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["usuario__username", "genero"]
    ordering_fields = ["id", "usuario__username", "genero"]

    def get_queryset(self):
        queryset = Dieta.objects.select_related("usuario", "objetivo", "nivel_atividade")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["id", "username"]
    ordering_fields = ["id", "username"]


class ImprimirDietaViewSet(viewsets.ModelViewSet):
    queryset = ImprimirDieta.objects.all()
    serializer_class = ImprimirDietaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["id", "usuario__username"]
    ordering_fields = ["id", "usuario__username"]

    def get_queryset(self):
        queryset = ImprimirDieta.objects.select_related("usuario").prefetch_related("itens")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

