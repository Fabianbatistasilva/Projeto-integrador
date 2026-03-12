from decimal import Decimal

from django.test import SimpleTestCase

from nutri.services.tmb_service import (
    TmbValidationError,
    parse_calculated_diet_values,
    validate_goal_and_activity_config,
    validate_basic_tmb_fields,
)


class TmbServiceTests(SimpleTestCase):
    def test_validate_basic_tmb_fields_requires_integer_height_without_decimal(self):
        with self.assertRaises(TmbValidationError):
            validate_basic_tmb_fields(
                {"peso": "80", "height": "1,75", "age": "30", "opcao": "Masculino"}
            )

    def test_validate_basic_tmb_fields_returns_normalized_values(self):
        result = validate_basic_tmb_fields(
            {"peso": "80", "height": "175", "age": "30", "opcao": "Masculino"}
        )
        self.assertEqual(result["peso"], 80)
        self.assertEqual(result["altura"], 175)
        self.assertEqual(result["idade"], 30)
        self.assertEqual(result["sexo"], "Masculino")

    def test_parse_calculated_diet_values_rejects_missing_payload(self):
        with self.assertRaises(TmbValidationError):
            parse_calculated_diet_values("")

    def test_parse_calculated_diet_values_requires_minimum_expected_shape(self):
        with self.assertRaises(TmbValidationError):
            parse_calculated_diet_values("0,0,0")

    def test_validate_goal_and_activity_config_accepts_canonical_values(self):
        objetivo = type("ObjetivoStub", (), {"slug": "cutting"})()
        atividade = type("AtividadeStub", (), {"slug": "moderado", "fator": Decimal("1.50")})()

        result = validate_goal_and_activity_config(objetivo, atividade)

        self.assertEqual(result["objetivo_slug"], "cutting")
        self.assertEqual(result["atividade_slug"], "moderado")
        self.assertEqual(result["atividade_fator"], Decimal("1.50"))

    def test_validate_goal_and_activity_config_rejects_invalid_goal_slug(self):
        objetivo = type("ObjetivoStub", (), {"slug": "ganho-rapido"})()
        atividade = type("AtividadeStub", (), {"slug": "moderado", "fator": Decimal("1.50")})()

        with self.assertRaises(TmbValidationError):
            validate_goal_and_activity_config(objetivo, atividade)

    def test_validate_goal_and_activity_config_rejects_non_positive_factor(self):
        objetivo = type("ObjetivoStub", (), {"slug": "bulking"})()
        atividade = type("AtividadeStub", (), {"slug": "leve", "fator": Decimal("0.00")})()

        with self.assertRaises(TmbValidationError):
            validate_goal_and_activity_config(objetivo, atividade)
