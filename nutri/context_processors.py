from nutri.models import Dieta


def navigation_goal_context(request):
    default_label = "Criar Dieta"
    user = getattr(request, "user", None)

    if not user or not user.is_authenticated:
        return {"nav_has_goal": False, "nav_goal_label": default_label}

    has_goal = Dieta.objects.filter(usuario_id=user.id, dieta=True).exists()
    return {
        "nav_has_goal": has_goal,
        "nav_goal_label": "Redefinir objetivo" if has_goal else default_label,
    }

