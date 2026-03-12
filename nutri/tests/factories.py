from django.contrib.auth.models import User

from nutri.models import Dieta, NivelAtividade, Objetivo


def make_user(username="user", password="pass1234"):
    user = User.objects.create_user(username=username, password=password)
    return user, password


def make_goal_and_activity():
    objetivo, _created = Objetivo.objects.get_or_create(
        slug="bulking",
        defaults={"objetivo": "Bulking", "ordem": 1},
    )
    atividade, _created = NivelAtividade.objects.get_or_create(
        slug="intenso",
        defaults={"atividade": "Bastante Ativo", "fator": "1.80", "ordem": 3},
    )
    return objetivo, atividade


def make_dieta_for_user(user, objetivo=None, atividade=None, dieta_flag=True):
    if objetivo is None or atividade is None:
        default_objetivo, default_atividade = make_goal_and_activity()
        objetivo = objetivo or default_objetivo
        atividade = atividade or default_atividade
    return Dieta.objects.create(
        usuario=user,
        objetivo=objetivo,
        peso=80,
        altura=175,
        idade=30,
        genero="Masculino",
        tmb=1800,
        gasto_dia=2600,
        caloria_dieta=2300,
        proteina=160,
        gordura=70,
        carboidratos=250,
        nivel_atividade=atividade,
        dieta=dieta_flag,
    )
