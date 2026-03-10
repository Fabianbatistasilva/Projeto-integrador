from django.urls import path, include
from . import views
from rest_framework import routers
from nutri.views import ImprimirDietaViewSet, DietaViewSet, UserViewSet

router = routers.DefaultRouter()

router.register(r'Users', UserViewSet)
router.register(r'ImprimirDietas', ImprimirDietaViewSet)
router.register(r'Dietas', DietaViewSet)

urlpatterns = [
    path('', views.index, name='home'),
    path('health/', views.healthcheck, name='healthcheck'),
    path('logar/', views.UserLogin, name='login_site'),
    path('registration/', views.UserRegistration, name='registration_screen'),
    path('logout/', views.UserLogout, name='logout'),
    path('introducao/', views.introducao, name='introducao'),
    path('criando_sua_dieta/', views.create_diet, name='criar_dieta'),
    path('api/alimentos/', views.taco_search, name='taco_search'),
    path('api/alimentos/criar/', views.taco_create, name='taco_create'),
    path('tmb/', views.tela_tmb, name='tela_tmb'),
    path('diet_screen/', views.diet_screen, name='diet_screen'),
    path('data/', include(router.urls)),
]
