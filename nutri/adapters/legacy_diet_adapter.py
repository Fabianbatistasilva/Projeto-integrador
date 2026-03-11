LEGACY_MAX_ITEMS_PER_MEAL = 3


def apply_legacy_fields(imprimir_dieta, meal_map, max_items_per_meal=LEGACY_MAX_ITEMS_PER_MEAL):
    for refeicao in range(1, 7):
        for ordem in range(1, max_items_per_meal + 1):
            sufixo = f"{refeicao}{ordem}"
            setattr(imprimir_dieta, f"ref_{sufixo}", "")
            setattr(imprimir_dieta, f"quant_{sufixo}", 0)
            setattr(imprimir_dieta, f"kcal_{sufixo}", 0)
            setattr(imprimir_dieta, f"prot_{sufixo}", 0)
            setattr(imprimir_dieta, f"gord_{sufixo}", 0)
            setattr(imprimir_dieta, f"carb_{sufixo}", 0)

        for ordem, item in enumerate(meal_map.get(refeicao, [])[:max_items_per_meal], start=1):
            sufixo = f"{refeicao}{ordem}"
            setattr(imprimir_dieta, f"ref_{sufixo}", item["alimento"])
            setattr(imprimir_dieta, f"quant_{sufixo}", item["quantidade"])
            setattr(imprimir_dieta, f"kcal_{sufixo}", item["kcal"])
            setattr(imprimir_dieta, f"prot_{sufixo}", item["prot"])
            setattr(imprimir_dieta, f"gord_{sufixo}", item["gord"])
            setattr(imprimir_dieta, f"carb_{sufixo}", item["carb"])

