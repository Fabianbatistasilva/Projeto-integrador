from django.test import TestCase

from nutri.models import ImprimirDieta
from nutri.services.diet_service import (
    DietPayloadValidationError,
    count_selected_items,
    normalize_meal_payload,
    parse_diet_payload_text,
    save_dynamic_diet,
)
from nutri.tests.factories import make_user


class DietServiceTests(TestCase):
    def setUp(self):
        self.user, _ = make_user("diet_service_user")

    def test_parse_diet_payload_text_rejects_invalid_json(self):
        with self.assertRaises(DietPayloadValidationError):
            parse_diet_payload_text("{invalid")

    def test_normalize_meal_payload_rejects_item_without_quantity(self):
        payload = {
            "selected_meals": 2,
            "meals": [{"refeicao": 1, "items": [{"name": "Arroz", "quantidade": 0}]}],
        }
        with self.assertRaises(DietPayloadValidationError):
            normalize_meal_payload(payload)

    def test_count_selected_items_counts_only_selected_range(self):
        meal_map = {
            1: [{"alimento": "A"}],
            2: [{"alimento": "B"}, {"alimento": "C"}],
            3: [{"alimento": "D"}],
            4: [],
            5: [],
            6: [],
        }
        self.assertEqual(count_selected_items(2, meal_map), 3)

    def test_save_dynamic_diet_persists_items_and_syncs_legacy_fields(self):
        meal_map = {
            1: [{"alimento": "Arroz", "quantidade": 200, "kcal": 260, "prot": 6, "carb": 56, "gord": 2}],
            2: [{"alimento": "Frango", "quantidade": 150, "kcal": 247, "prot": 46, "carb": 0, "gord": 6}],
            3: [],
            4: [],
            5: [],
            6: [],
        }

        save_dynamic_diet(self.user.id, meal_map)

        dieta = ImprimirDieta.objects.get(usuario=self.user)
        self.assertEqual(dieta.itens.count(), 2)
        self.assertEqual(dieta.ref_11, "Arroz")
        self.assertEqual(dieta.quant_11, 200)
        self.assertEqual(dieta.ref_21, "Frango")
        self.assertEqual(dieta.quant_21, 150)

