from django.urls import path
from . import views
urlpatterns =[
    path('',views.index,name='home'),
    path('login/',views.UserLogin, name='login'),
    path('introducao/',views.introducao, name='introducao'),
]
