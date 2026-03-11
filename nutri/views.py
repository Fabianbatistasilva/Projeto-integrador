from django.core.cache import cache
from django.db import connection

from nutri.views_api import DietaViewSet, ImprimirDietaViewSet, UserViewSet
from nutri.views_auth import UserLogin, UserLogout, UserRegistration
from nutri.views_diet import create_diet, diet_screen, index, introducao, tela_tmb
from nutri.views_health import healthcheck
from nutri.views_taco import fetch_taco_alimentos, taco_create, taco_search

__all__ = [
    "DietaViewSet",
    "ImprimirDietaViewSet",
    "UserViewSet",
    "UserLogin",
    "UserLogout",
    "UserRegistration",
    "index",
    "introducao",
    "create_diet",
    "taco_search",
    "taco_create",
    "tela_tmb",
    "diet_screen",
    "healthcheck",
    "fetch_taco_alimentos",
    "cache",
    "connection",
]

