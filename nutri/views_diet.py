from django.contrib import messages
from django.shortcuts import redirect, render

from nutri.models import Dieta, ImprimirDieta, NivelAtividade, Objetivo
from nutri.services.common import parse_int_or_zero
from nutri.services.diet_service import (
    DietPayloadValidationError,
    build_meals_for_screen,
    count_selected_items,
    get_meal_card_definitions,
    normalize_meal_payload,
    parse_diet_payload_text,
    save_dynamic_diet,
)
from nutri.services.tmb_service import (
    TmbValidationError,
    parse_calculated_diet_values,
    validate_basic_tmb_fields,
    validate_goal_and_activity_config,
)
from nutri.views_taco import fetch_taco_alimentos, is_taco_configured


def index(request):
    return render(request, "paginas/home.html")


def introducao(request):
    if request.user.is_authenticated:
        has_dieta = Dieta.objects.filter(usuario_id=request.user.id, dieta=True).exists()
        return render(request, "paginas/introdução_dieta.html", {"veri_dieta": has_dieta})
    return render(request, "paginas/introdução_dieta.html")


def create_diet(request):
    if request.user.is_authenticated is False:
        return redirect("login_site")

    pesquisa = (request.GET.get("txtbuscar") or "").strip()
    requested_page = parse_int_or_zero(request.GET.get("page"))
    page = requested_page if requested_page > 0 else 1
    taco = fetch_taco_alimentos(pesquisa if pesquisa else None, page=page)

    dados = Dieta.objects.filter(usuario_id=request.user.id).first()
    if not dados:
        messages.info(request, "Preencha os dados de objetivo antes de montar a dieta.")
        return redirect("tela_tmb")

    if request.method == "POST":
        try:
            payload = parse_diet_payload_text(request.POST.get("diet_payload", ""))
            selected_meals, meal_map = normalize_meal_payload(payload)
        except DietPayloadValidationError as error:
            messages.info(request, str(error))
            return redirect("criar_dieta")

        total_itens = count_selected_items(selected_meals, meal_map)
        if total_itens == 0:
            messages.info(request, "Adicione alimentos para montar sua dieta.")
            return redirect("criar_dieta")

        save_dynamic_diet(request.user.id, meal_map)
        return redirect("diet_screen")

    return render(
        request,
        "paginas/create_diet.html",
        {
            "taco": taco,
            "dados": dados,
            "taco_configured": is_taco_configured(),
            "meal_cards": get_meal_card_definitions(),
        },
    )


def tela_tmb(request):
    if request.user.is_authenticated is False:
        return redirect("login_site")

    objetivos = Objetivo.objects.order_by("ordem", "objetivo")
    niveis_atividade = NivelAtividade.objects.order_by("ordem", "atividade")
    ver_user = Dieta.objects.filter(usuario_id=request.user.id).first()

    if request.method == "POST":
        objetivo_id = parse_int_or_zero(request.POST.get("objetivo_user"))
        nivel_atividade_id = parse_int_or_zero(request.POST.get("nivel_de_ati_user"))

        if objetivo_id <= 0 or nivel_atividade_id <= 0:
            messages.info(request, "Selecione objetivo e nivel de atividade.")
            return redirect("tela_tmb")

        objetivo = Objetivo.objects.filter(id=objetivo_id).first()
        nivel_atividade = NivelAtividade.objects.filter(id=nivel_atividade_id).first()
        if not objetivo or not nivel_atividade:
            messages.info(request, "Objetivo ou nivel de atividade invalido.")
            return redirect("tela_tmb")

        try:
            base_fields = validate_basic_tmb_fields(request.POST)
            validate_goal_and_activity_config(objetivo, nivel_atividade)
            calculated_values = parse_calculated_diet_values(request.POST.get("local_dados_do_user"))
        except TmbValidationError as error:
            messages.info(request, str(error))
            return redirect("tela_tmb")

        payload = {
            "objetivo_id": objetivo_id,
            "peso": base_fields["peso"],
            "altura": base_fields["altura"],
            "idade": base_fields["idade"],
            "genero": base_fields["sexo"],
            "tmb": calculated_values[0],
            "gasto_dia": calculated_values[1],
            "caloria_dieta": calculated_values[2],
            "proteina": calculated_values[3],
            "gordura": calculated_values[4],
            "carboidratos": calculated_values[5],
            "nivel_atividade_id": nivel_atividade_id,
            "dieta": True,
        }

        updated = Dieta.objects.filter(usuario_id=request.user.id).update(**payload)
        if updated == 0:
            Dieta.objects.create(usuario_id=request.user.id, **payload)

        return redirect("criar_dieta")

    return render(
        request,
        "paginas/tela_tmb.html",
        {"objetivo": objetivos, "nivel_at": niveis_atividade, "verUser": ver_user},
    )


def diet_screen(request):
    if request.user.is_authenticated is False:
        messages.info(request, "Faca o Login")
        return redirect("login_site")

    dieta = ImprimirDieta.objects.filter(usuario_id=request.user.id).first()
    if not dieta:
        verificar_tmb = Dieta.objects.filter(usuario_id=request.user.id).exists()
        if verificar_tmb:
            messages.info(request, "Faca as refeicoes")
            return redirect("criar_dieta")
        messages.info(request, "Preencha os dados")
        return redirect("tela_tmb")

    meals, total_caloria, total_proteina, total_carboidratos, total_gordura = build_meals_for_screen(dieta)
    total_quantidade = sum(meal.get("subtotal_qtd", 0) for meal in meals)

    perfil_base = (
        Dieta.objects.select_related("objetivo", "nivel_atividade")
        .filter(usuario_id=request.user.id)
        .first()
    )

    objetivo_nome = ""
    nivel_atividade_nome = ""
    peso_usuario = None
    altura_usuario = None
    idade_usuario = None
    gasto_dia = None

    if perfil_base:
        if perfil_base.objetivo_id:
            objetivo_nome = perfil_base.objetivo.objetivo
        if perfil_base.nivel_atividade_id:
            nivel_atividade_nome = perfil_base.nivel_atividade.atividade
        peso_usuario = perfil_base.peso
        altura_usuario = perfil_base.altura
        idade_usuario = perfil_base.idade
        gasto_dia = perfil_base.gasto_dia

    return render(
        request,
        "paginas/diet_screen.html",
        {
            "meals": meals,
            "total_caloria": total_caloria,
            "total_proteina": total_proteina,
            "total_carboidratos": total_carboidratos,
            "total_gordura": total_gordura,
            "total_quantidade": total_quantidade,
            "objetivo_nome": objetivo_nome,
            "nivel_atividade_nome": nivel_atividade_nome,
            "peso_usuario": peso_usuario,
            "altura_usuario": altura_usuario,
            "idade_usuario": idade_usuario,
            "gasto_dia": gasto_dia,
        },
    )
