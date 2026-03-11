import json

from django.db import transaction

from nutri.adapters.legacy_diet_adapter import apply_legacy_fields
from nutri.models import ImprimirDieta, ItemRefeicao
from nutri.services.common import parse_int_or_zero


MEAL_SUFFIXES = {
    1: "one",
    2: "two",
    3: "tree",
    4: "four",
    5: "five",
    6: "six",
}


class DietPayloadValidationError(ValueError):
    pass


def get_meal_card_definitions():
    return [
        {"number": meal_number, "suffix": MEAL_SUFFIXES[meal_number]}
        for meal_number in range(1, 7)
    ]


def parse_diet_payload_text(raw_payload):
    payload_text = str(raw_payload or "").strip()
    if payload_text == "":
        raise DietPayloadValidationError("Nao foi possivel ler os dados da dieta.")

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise DietPayloadValidationError("Formato da dieta invalido.") from exc

    if not isinstance(payload, dict):
        raise DietPayloadValidationError("Formato da dieta invalido.")

    return payload


def _calculate_meal_item(alimento, quantidade, proteina, gordura, carboidratos, kcal):
    alimentos = str(alimento or "").strip()
    quantidades = parse_int_or_zero(quantidade)
    proteinas = parse_int_or_zero(proteina)
    gorduras = parse_int_or_zero(gordura)
    carbo = parse_int_or_zero(carboidratos)
    kcals = parse_int_or_zero(kcal)

    if quantidades <= 0 or alimentos == "":
        return {"alimento": "", "quantidade": 0, "kcal": 0, "prot": 0, "carb": 0, "gord": 0}

    return {
        "alimento": alimentos,
        "quantidade": quantidades,
        "kcal": int((quantidades / 100) * kcals),
        "prot": int((quantidades / 100) * proteinas),
        "carb": int((quantidades / 100) * carbo),
        "gord": int((quantidades / 100) * gorduras),
    }


def normalize_meal_payload(payload):
    selected_meals = parse_int_or_zero(payload.get("selected_meals"))
    if selected_meals < 2 or selected_meals > 6:
        selected_meals = 6

    meals_payload = payload.get("meals")
    if not isinstance(meals_payload, list):
        meals_payload = []

    normalized = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for meal in meals_payload:
        if not isinstance(meal, dict):
            continue

        refeicao = parse_int_or_zero(meal.get("refeicao"))
        if refeicao < 1 or refeicao > 6:
            continue

        raw_items = meal.get("items")
        if not isinstance(raw_items, list):
            continue

        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue

            alimento = str(raw_item.get("name", "") or "").strip()
            quantidade = parse_int_or_zero(raw_item.get("quantidade"))
            kcal_base = parse_int_or_zero(raw_item.get("kcal_base"))
            prot_base = parse_int_or_zero(raw_item.get("prot_base"))
            gord_base = parse_int_or_zero(raw_item.get("gord_base"))
            carb_base = parse_int_or_zero(raw_item.get("carb_base"))

            if not alimento and quantidade <= 0:
                continue

            if alimento == "" or quantidade <= 0:
                raise DietPayloadValidationError("Revise os alimentos e quantidades antes de salvar.")

            normalized[refeicao].append(
                _calculate_meal_item(
                    alimento,
                    quantidade,
                    prot_base,
                    gord_base,
                    carb_base,
                    kcal_base,
                )
            )

    return selected_meals, normalized


def count_selected_items(selected_meals, meal_map):
    total_items = 0
    for refeicao in range(1, selected_meals + 1):
        total_items += len(meal_map.get(refeicao, []))
    return total_items


@transaction.atomic
def save_dynamic_diet(user_id, meal_map):
    imprimir_dieta = ImprimirDieta.objects.filter(usuario_id=user_id).first()
    if not imprimir_dieta:
        imprimir_dieta = ImprimirDieta.objects.create(
            usuario_id=user_id,
            ref_11="",
            ref_12="",
            ref_13="",
            ref_21="",
            ref_22="",
            ref_23="",
        )

    imprimir_dieta.itens.all().delete()

    novos_itens = []
    for refeicao in range(1, 7):
        for ordem, item in enumerate(meal_map.get(refeicao, []), start=1):
            novos_itens.append(
                ItemRefeicao(
                    dieta=imprimir_dieta,
                    refeicao=refeicao,
                    ordem=ordem,
                    alimento=item["alimento"],
                    quantidade=item["quantidade"],
                    kcal=item["kcal"],
                    prot=item["prot"],
                    gord=item["gord"],
                    carb=item["carb"],
                )
            )

    if novos_itens:
        ItemRefeicao.objects.bulk_create(novos_itens)

    apply_legacy_fields(imprimir_dieta, meal_map)
    imprimir_dieta.save()


def _legacy_item_dict(dieta, refeicao, ordem):
    sufixo = f"{refeicao}{ordem}"
    nome = str(getattr(dieta, f"ref_{sufixo}", "") or "").strip()
    quantidade = parse_int_or_zero(getattr(dieta, f"quant_{sufixo}", 0))
    kcal = parse_int_or_zero(getattr(dieta, f"kcal_{sufixo}", 0))
    prot = parse_int_or_zero(getattr(dieta, f"prot_{sufixo}", 0))
    gord = parse_int_or_zero(getattr(dieta, f"gord_{sufixo}", 0))
    carb = parse_int_or_zero(getattr(dieta, f"carb_{sufixo}", 0))

    if nome == "" or quantidade <= 0:
        return None

    return {
        "nome": nome,
        "quantidade": quantidade,
        "kcal": kcal,
        "prot": prot,
        "gord": gord,
        "carb": carb,
    }


def build_meals_for_screen(dieta):
    meals = []
    total_kcal = 0
    total_prot = 0
    total_carb = 0
    total_gord = 0

    related_items = list(dieta.itens.all().order_by("refeicao", "ordem", "id"))
    grouped = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}

    if related_items:
        for item in related_items:
            grouped[item.refeicao].append(
                {
                    "nome": item.alimento,
                    "quantidade": item.quantidade,
                    "kcal": item.kcal,
                    "prot": item.prot,
                    "gord": item.gord,
                    "carb": item.carb,
                }
            )
    else:
        for refeicao in range(1, 7):
            for ordem in range(1, 4):
                legacy_item = _legacy_item_dict(dieta, refeicao, ordem)
                if legacy_item:
                    grouped[refeicao].append(legacy_item)

    for refeicao in range(1, 7):
        itens = grouped[refeicao]
        if not itens:
            continue

        subtotal_kcal = sum(item["kcal"] for item in itens)
        subtotal_qtd = sum(item["quantidade"] for item in itens)
        subtotal_prot = sum(item["prot"] for item in itens)
        subtotal_carb = sum(item["carb"] for item in itens)
        subtotal_gord = sum(item["gord"] for item in itens)

        meals.append(
            {
                "numero": refeicao,
                "itens": itens,
                "subtotal_qtd": subtotal_qtd,
                "subtotal_kcal": subtotal_kcal,
                "subtotal_prot": subtotal_prot,
                "subtotal_carb": subtotal_carb,
                "subtotal_gord": subtotal_gord,
            }
        )

        total_kcal += subtotal_kcal
        total_prot += subtotal_prot
        total_carb += subtotal_carb
        total_gord += subtotal_gord

    return meals, total_kcal, total_prot, total_carb, total_gord

